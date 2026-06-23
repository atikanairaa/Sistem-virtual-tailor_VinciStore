from enum import Enum


class BodyShape(str, Enum):
    """
    Body shape labels.
    Values must exactly match what the KNN model (model_knn_shape.pkl) was trained to output.
    Actual model classes: ['Apple', 'Inverted Triangle', 'Rectangle']
    """
    APPLE             = "Apple"
    INVERTED_TRIANGLE = "Inverted Triangle"
    RECTANGLE         = "Rectangle"
    UNKNOWN           = "Unknown"

    def __str__(self):
        return self.value