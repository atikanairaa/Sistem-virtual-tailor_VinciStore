from enum import Enum


class FitType(str, Enum):
    """
    Fit recommendation labels.
    Values must exactly match what the KNN model (model_knn_fit.pkl) was trained to output.
    Actual model classes: ['Not Recommended', 'Oversize Fit', 'Regular Fit', 'Tight Fit']
    """
    REGULAR_FIT       = "Regular Fit"
    OVERSIZE_FIT      = "Oversize Fit"
    TIGHT_FIT         = "Tight Fit"
    NOT_RECOMMENDED   = "Not Recommended"
    UNKNOWN           = "Unknown"

    def __str__(self):
        return self.value