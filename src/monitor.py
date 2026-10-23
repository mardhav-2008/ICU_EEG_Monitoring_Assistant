from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pyarrow.parquet as pq

from assistant import (
    get_attention_level,
    get_top_alternatives,
    get_uncertainty_level,
)
from inference import (
    LABELS,
    EEG_SAMPLING_RATE,
    EEG_WINDOW_SECONDS,
    SPEC_WINDOW_SECONDS,
    load_recording,
    predict_loaded,
)


WINDOW_SECONDS = EEG_WINDOW_SECONDS
STEP_SECONDS = 10


def get_eeg_duration(eeg_path):
    """Return the recording duration in seconds."""

    num_samples = pq.ParquetFile(eeg_path).metadata.num_rows

    return num_samples / EEG_SAMPLING_RATE


def analyze_window(
    eeg,
    spectrogram,
    spectrogram_times,
    offset,
    duration,
):
    """Run the model on one monitoring window."""

    prediction, probability_array = predict_loaded(
        eeg,
        spectrogram,
        spectrogram_times,
        offset,
    )

    probabilities = dict(
        zip(
            LABELS,
            probability_array,
        )
    )

    confidence = float(probabilities[prediction])

    uncertainty = get_uncertainty_level(
        confidence,
        probabilities,
    )

    attention = get_attention_level(
        prediction,
        confidence,
        uncertainty,
    )

    eeg_start = offset
    eeg_end = min(
        offset + WINDOW_SECONDS,
        duration,
    )

    spectrogram_start = max(
        0,
        offset - SPEC_WINDOW_SECONDS / 2,
    )

    spectrogram_end = min(
        duration,
        offset + SPEC_WINDOW_SECONDS / 2,
    )

    return {
        "prediction": prediction,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "attention": attention,
        "alternatives": get_top_alternatives(
            probabilities,
            prediction,
        ),
        "probabilities": probabilities,
        "eeg_start": eeg_start,
        "eeg_end": eeg_end,
        "spectrogram_start": spectrogram_start,
        "spectrogram_end": spectrogram_end,
    }


def monitor_recording(
    eeg,
    spectrogram,
    spectrogram_times,
    duration,
):
    """Run inference across the recording."""

    results = []

    for start in range(
        0,
        int(duration),
        STEP_SECONDS,
    ):
        result = analyze_window(
            eeg,
            spectrogram,
            spectrogram_times,
            start,
            duration,
        )

        results.append(result)

    return results


def build_event(
    pattern,
    start_time,
    end_time,
    results,
):
    """Create a summary for one continuous pattern."""

    confidences = [result["confidence"] for result in results]

    return {
        "pattern": pattern,
        "start": start_time,
        "end": end_time,
        "duration": end_time - start_time,
        "average_confidence": (sum(confidences) / len(confidences)),
        "max_confidence": max(confidences),
    }


def detect_events(
    results,
    recording_duration,
):
    """Group consecutive windows with the same prediction."""

    if not results:
        return []

    events = []

    current_pattern = results[0]["prediction"]
    current_results = [results[0]]
    start_time = results[0]["eeg_start"]

    for result in results[1:]:
        if result["prediction"] == current_pattern:
            current_results.append(result)
            continue

        events.append(
            build_event(
                current_pattern,
                start_time,
                result["eeg_start"],
                current_results,
            )
        )

        current_pattern = result["prediction"]
        current_results = [result]
        start_time = result["eeg_start"]

    events.append(
        build_event(
            current_pattern,
            start_time,
            recording_duration,
            current_results,
        )
    )

    return events


def detect_alerts(events):
    """
    Generate one alert for each continuous seizure event.

    Alerts are based on average confidence and observed
    event duration rather than individual windows.
    """

    alerts = []

    for event in events:
        if event["pattern"] != "Seizure":
            continue

        confidence = event["average_confidence"]
        duration = event["duration"]

        if confidence < 0.50:
            level = "REVIEW"

        elif confidence < 0.80:
            level = "ATTENTION"

        elif duration >= 20:
            level = "PERSISTENT HIGH"

        else:
            level = "HIGH"

        alerts.append(
            {
                "time": event["start"],
                "level": level,
                "reason": "Seizure prediction",
                "duration": duration,
                "confidence": confidence,
            }
        )

    return alerts


def print_timeline(results):
    print("\n" + "=" * 72)
    print("MONITORING TIMELINE")
    print("=" * 72)

    for result in results:
        print(
            f"{format_time(result['eeg_start'])} - "
            f"{format_time(result['eeg_end'])}  "
            f"{result['prediction']:<8} "
            f"{result['confidence']:>6.2%}  "
            f"{result['uncertainty']:<8} "
            f"{result['attention']}"
        )


def print_events(events):
    print("\n" + "=" * 72)
    print("PERSISTENT PATTERNS")
    print("=" * 72)

    if not events:
        print("NONE")
        return

    for event in events:
        print(
            f"{format_time(event['start'])} - "
            f"{format_time(event['end'])}  "
            f"{event['pattern']}"
        )

        print(f"Duration: {event['duration']:.0f} seconds")

        print(f"Average confidence: {event['average_confidence']:.2%}")

        print(f"Maximum confidence: {event['max_confidence']:.2%}")


def print_alerts(alerts):
    print("\n" + "=" * 72)
    print("ALERTS")
    print("=" * 72)

    if not alerts:
        print("NONE")
        return

    for alert in alerts:
        print(f"{format_time(alert['time'])}  {alert['level']:<16} {alert['reason']}")

        print(f"Duration: {alert['duration']:.0f} seconds")

        print(f"Average confidence: {alert['confidence']:.2%}")


def print_dashboard(
    results,
    events,
    alerts,
    duration,
):
    """Print a compact monitoring summary."""

    if not results:
        print("No monitoring results.")
        return

    latest = results[-1]

    predictions = [result["prediction"] for result in results]

    counts = pd.Series(predictions).value_counts()

    dominant = counts.index[0]

    print("\n")
    print("=" * 72)
    print("                    ICU EEG MONITORING")
    print("=" * 72)

    print(f"Recording duration: {format_time(duration)}")

    print(f"Windows analyzed:   {len(results)}")

    print("-" * 72)

    print(f"Current pattern:    {latest['prediction']}")

    print(f"Confidence:         {latest['confidence']:.1%}")

    print(f"Uncertainty:        {latest['uncertainty']}")

    print(f"Attention:          {latest['attention']}")

    print("-" * 72)

    print(f"Dominant pattern:   {dominant}")

    print(f"Events detected:    {len(events)}")

    print(f"Alerts:             {len(alerts)}")

    print("-" * 72)
    print("PATTERN DISTRIBUTION")

    for pattern, count in counts.items():
        percentage = count / len(results)

        bar = "█" * int(percentage * 30)

        print(f"{pattern:<10} {bar:<30} {percentage:>5.1%}")

    print("-" * 72)

    if alerts:
        print("LATEST ALERT")

        alert = alerts[-1]

        print(f"{format_time(alert['time'])}  {alert['level']}")

        print(f"Reason: {alert['reason']}")

    else:
        print("ALERTS: NONE")

    print("=" * 72)


def save_results(results, eeg_id):
    """Save window-level monitoring results."""

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    rows = []

    for result in results:
        rows.append(
            {
                "eeg_start": result["eeg_start"],
                "eeg_end": result["eeg_end"],
                "spectrogram_start": (result["spectrogram_start"]),
                "spectrogram_end": (result["spectrogram_end"]),
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "uncertainty": result["uncertainty"],
                "attention": result["attention"],
            }
        )

    output_path = output_dir / f"monitoring_{eeg_id}.csv"

    pd.DataFrame(rows).to_csv(
        output_path,
        index=False,
    )

    return output_path


def save_plot(results, eeg_id):
    """Save the monitoring confidence timeline."""

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    times = [result["eeg_start"] for result in results]

    confidence = [result["confidence"] for result in results]

    labels = [result["prediction"] for result in results]

    plt.figure(figsize=(12, 6))

    plt.plot(
        times,
        confidence,
        marker="o",
        linewidth=2,
    )

    for time, conf, label in zip(
        times,
        confidence,
        labels,
    ):
        plt.annotate(
            label,
            (time, conf),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )

    plt.axhline(
        0.80,
        linestyle="--",
        alpha=0.5,
        label="High confidence",
    )

    plt.axhline(
        0.50,
        linestyle="--",
        alpha=0.5,
        label="Review threshold",
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Model confidence")
    plt.title("ICU EEG Monitoring Timeline")

    plt.ylim(0, 1)
    plt.grid(
        True,
        alpha=0.25,
    )

    plt.legend()

    output_path = output_dir / f"monitoring_{eeg_id}.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


def format_time(seconds):
    """Format seconds as MM:SS."""

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    return f"{minutes:02d}:{seconds:02d}"


def main():
    eeg_id = "4281533846"
    spectrogram_id = "274507067"

    eeg_path = Path("data/raw/train_eegs") / f"{eeg_id}.parquet"

    spectrogram_path = Path("data/raw/train_spectrograms") / f"{spectrogram_id}.parquet"

    duration = get_eeg_duration(eeg_path)

    print("\n" + "=" * 72)
    print("ICU EEG MONITORING SYSTEM")
    print("=" * 72)

    print(f"EEG:          {eeg_id}")

    print(f"Spectrogram:  {spectrogram_id}")

    print(f"Duration:     {duration:.1f} seconds")

    print(f"EEG window:   {WINDOW_SECONDS} seconds")

    print(f"Spectrogram:  {SPEC_WINDOW_SECONDS} seconds")

    print(f"Step:         {STEP_SECONDS} seconds")

    eeg, spectrogram, spectrogram_times = load_recording(
        eeg_path,
        spectrogram_path,
    )

    results = monitor_recording(
        eeg,
        spectrogram,
        spectrogram_times,
        duration,
    )

    events = detect_events(
        results,
        duration,
    )

    alerts = detect_alerts(events)

    print_timeline(results)
    print_events(events)
    print_alerts(alerts)

    print_dashboard(
        results,
        events,
        alerts,
        duration,
    )

    csv_path = save_results(
        results,
        eeg_id,
    )

    plot_path = save_plot(
        results,
        eeg_id,
    )

    print(f"\nSaved results: {csv_path}")

    print(f"Saved plot:    {plot_path}")

    print(
        "\nNote: This is a research/decision-support "
        "system and is not a clinical diagnosis."
    )


if __name__ == "__main__":
    main()
