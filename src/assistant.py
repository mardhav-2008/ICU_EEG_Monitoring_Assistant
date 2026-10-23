import argparse

from inference import predict


# ============================================================
# Thresholds
# ============================================================

HIGH_CONFIDENCE = 0.80
MODERATE_CONFIDENCE = 0.60

HIGH_UNCERTAINTY = 0.50
MODERATE_UNCERTAINTY = 0.70

CLOSE_MARGIN = 0.10


# ============================================================
# Attention / alert logic
# ============================================================


def get_uncertainty_level(confidence, probabilities):
    """
    Estimate uncertainty using both confidence and competition
    from the second-most likely class.
    """

    sorted_probabilities = sorted(
        probabilities.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    top_probability = sorted_probabilities[0][1]
    second_probability = sorted_probabilities[1][1]

    margin = top_probability - second_probability

    if top_probability < HIGH_UNCERTAINTY:
        return "HIGH"

    if margin < CLOSE_MARGIN:
        return "HIGH"

    if top_probability < MODERATE_UNCERTAINTY:
        return "MODERATE"

    if margin < 0.20:
        return "MODERATE"

    return "LOW"


def get_attention_level(predicted_class, confidence, uncertainty):
    """
    Determine how much attention the prediction deserves.

    Attention is intentionally separate from confidence.

    A low-confidence seizure prediction can still require
    HIGH attention because seizure is clinically important.
    """

    if predicted_class == "Seizure":
        if uncertainty == "HIGH":
            return "HIGH"

        if confidence >= HIGH_CONFIDENCE:
            return "CRITICAL"

        return "HIGH"

    if predicted_class in {"GPD", "LRDA", "LPD"}:
        if uncertainty == "HIGH":
            return "HIGH"

        if confidence >= HIGH_CONFIDENCE:
            return "MODERATE"

        return "MODERATE"

    # Other / GRDA
    if uncertainty == "HIGH":
        return "MODERATE"

    if confidence >= HIGH_CONFIDENCE:
        return "LOW"

    return "MODERATE"


# ============================================================
# Interpretation
# ============================================================


def get_interpretation(predicted_class):

    interpretations = {
        "Seizure": "The model predicts a seizure-related EEG pattern.",
        "GPD": "The model predicts generalized periodic discharges (GPD).",
        "LRDA": "The model predicts lateralized rhythmic delta activity (LRDA).",
        "Other": "The model predicts an EEG pattern outside the primary named categories.",
        "GRDA": "The model predicts generalized rhythmic delta activity (GRDA).",
        "LPD": "The model predicts lateralized periodic discharges (LPD).",
    }

    return interpretations.get(
        predicted_class,
        "The model predicts an unspecified EEG pattern.",
    )


# ============================================================
# Alternatives
# ============================================================


def get_top_alternatives(probabilities, predicted_class, n=2):

    alternatives = [
        (label, probability)
        for label, probability in probabilities.items()
        if label != predicted_class
    ]

    alternatives.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return alternatives[:n]


# ============================================================
# Uncertainty explanation
# ============================================================


def get_uncertainty_message(
    predicted_class,
    confidence,
    probabilities,
):

    alternatives = get_top_alternatives(
        probabilities,
        predicted_class,
        n=1,
    )

    if not alternatives:
        return "No competing prediction available."

    second_class, second_probability = alternatives[0]

    margin = confidence - second_probability

    if confidence < HIGH_UNCERTAINTY:
        return f"The model is uncertain between {predicted_class} and {second_class}."

    if margin < CLOSE_MARGIN:
        return f"The model has a close competing prediction: {second_class}."

    if confidence < MODERATE_CONFIDENCE:
        return f"The model has moderate confidence in {predicted_class}."

    return f"The model has relatively strong confidence in this prediction."


# ============================================================
# Attention explanation
# ============================================================


def get_attention_message(
    predicted_class,
    confidence,
    uncertainty,
    attention,
):

    if predicted_class == "Seizure":
        if uncertainty == "HIGH":
            return (
                "Seizure prediction requires attention despite high model uncertainty."
            )

        if confidence >= HIGH_CONFIDENCE:
            return (
                "High-confidence seizure prediction. Immediate review is recommended."
            )

        return "Possible seizure-related pattern detected. Review is recommended."

    if attention == "HIGH":
        return "The prediction is uncertain and should be reviewed alongside the EEG."

    if attention == "MODERATE":
        return (
            "The pattern is relevant for monitoring but does "
            "not meet the seizure alert criteria."
        )

    return "The model predicts this pattern with relatively low monitoring priority."


# ============================================================
# Main analysis
# ============================================================


def analyze_prediction(
    eeg_path,
    spectrogram_path,
    offset_seconds=0.0,
):

    predicted_class, probability_array = predict(
        eeg_path,
        spectrogram_path,
        offset_seconds,
        offset_seconds,
    )

    labels = [
        "Seizure",
        "GPD",
        "LRDA",
        "Other",
        "GRDA",
        "LPD",
    ]

    probabilities = {
        label: float(probability_array[index]) for index, label in enumerate(labels)
    }

    confidence = probabilities[predicted_class]

    uncertainty = get_uncertainty_level(
        confidence,
        probabilities,
    )

    attention = get_attention_level(
        predicted_class,
        confidence,
        uncertainty,
    )

    alternatives = get_top_alternatives(
        probabilities,
        predicted_class,
    )

    interpretation = get_interpretation(
        predicted_class,
    )

    uncertainty_message = get_uncertainty_message(
        predicted_class,
        confidence,
        probabilities,
    )

    attention_message = get_attention_message(
        predicted_class,
        confidence,
        uncertainty,
        attention,
    )

    return {
        "prediction": predicted_class,
        "confidence": confidence,
        "probabilities": probabilities,
        "uncertainty": uncertainty,
        "attention": attention,
        "alternatives": alternatives,
        "interpretation": interpretation,
        "uncertainty_message": uncertainty_message,
        "attention_message": attention_message,
    }


# ============================================================
# CLI
# ============================================================


def main():

    parser = argparse.ArgumentParser(description="ICU EEG Monitoring Assistant")

    parser.add_argument(
        "--eeg",
        type=int,
        required=True,
        help="EEG ID",
    )

    parser.add_argument(
        "--spectrogram",
        type=int,
        required=True,
        help="Spectrogram ID",
    )

    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Window offset in seconds",
    )

    args = parser.parse_args()

    eeg_path = f"data/raw/train_eegs/{args.eeg}.parquet"

    spectrogram_path = f"data/raw/train_spectrograms/{args.spectrogram}.parquet"

    result = analyze_prediction(
        eeg_path,
        spectrogram_path,
        args.offset,
    )

    print()
    print("=" * 60)
    print("ICU EEG MONITORING ASSISTANT")
    print("=" * 60)

    print(f"EEG ID:          {args.eeg}")
    print(f"Spectrogram ID:  {args.spectrogram}")
    print(f"Offset:          {args.offset} seconds")

    print()

    print(f"Predicted pattern: {result['prediction']}")

    print(f"Confidence:        {result['confidence']:.2%}")

    print(f"Uncertainty:       {result['uncertainty']}")

    print(f"Attention level:   {result['attention']}")

    print()

    print("Top alternatives:")

    for label, probability in result["alternatives"]:
        print(f"  {label:<10} {probability:.2%}")

    print()

    print("Interpretation:")
    print(f"  {result['interpretation']}")

    print()

    print("Uncertainty assessment:")
    print(f"  {result['uncertainty_message']}")

    print()

    print("Monitoring assessment:")
    print(f"  {result['attention_message']}")

    print()

    print(
        "Note: This is a research/decision-support "
        "model and is not a clinical diagnosis."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
