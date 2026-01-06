# tools/heart_disease_model.py
"""
Heart Disease Prediction ML Tool.
Uses trained ML model to predict heart disease risk based on patient data.
"""

import logging
import pickle
import numpy as np
from typing import Dict, Any, List
from pathlib import Path
from langchain.tools import tool
from langchain.agents import ToolRuntime
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Cache the model at module level
_model = None


def load_model():
    """Load the heart disease prediction model (cached)."""
    global _model
    if _model is not None:
        return _model
    
    model_path = Path(HEART_DISEASE_MODEL_PATH)
    if not model_path.exists():
        logger.warning(f"Heart disease model not found at {settings.HEART_DISEASE_MODEL_PATH}")
        return None
    
    try:
        with open(model_path, 'rb') as f:
            _model = pickle.load(f)
        logger.info(f"Heart disease model loaded from {settings.HEART_DISEASE_MODEL_PATH}")
        return _model
    except Exception as e:
        logger.error(f"Failed to load heart disease model: {e}")
        return None


@tool("predict_heart_disease_risk", description="Predict heart disease risk based on patient data: age, sex, chest pain type, blood pressure, cholesterol, fasting blood sugar, resting ECG, max heart rate, exercise angina, ST depression, slope, vessels, thalassemia. Returns risk probability and recommendations.")
def predict_heart_disease_risk(
    runtime: ToolRuntime,
    age: int,
    sex: int,  # 1=male, 0=female
    chest_pain_type: int,  # 0-3
    resting_bp: int,  # mm Hg
    cholesterol: int,  # mg/dl
    fasting_blood_sugar: int,  # 1 if >120 mg/dl, else 0
    resting_ecg: int,  # 0-2
    max_heart_rate: int,
    exercise_angina: int,  # 1=yes, 0=no
    oldpeak: float,  # ST depression
    slope: int,  # 0-2
    vessels: int,  # 0-3
    thal: int  # 1=normal, 2=fixed defect, 3=reversible defect
) -> Dict[str, Any]:
    """
    Predict heart disease risk using ML model.
    
    Args:
        runtime: Tool runtime context
        age: Patient age
        sex: 1=male, 0=female
        chest_pain_type: Type of chest pain (0-3)
        resting_bp: Resting blood pressure (mm Hg)
        cholesterol: Serum cholesterol (mg/dl)
        fasting_blood_sugar: 1 if >120 mg/dl, else 0
        resting_ecg: Resting ECG results (0-2)
        max_heart_rate: Maximum heart rate achieved
        exercise_angina: Exercise induced angina (1=yes, 0=no)
        oldpeak: ST depression induced by exercise
        slope: Slope of peak exercise ST segment (0-2)
        vessels: Number of major vessels colored by fluoroscopy (0-3)
        thal: Thalassemia (1=normal, 2=fixed defect, 3=reversible defect)
    
    Returns:
        Dict with risk prediction and recommendations
    """
    model = load_model()
    
    if model is None:
        return {
            "error": "Heart disease prediction model not available",
            "message": "Model file not found or failed to load",
            "instructions": [
                "1. Train a heart disease model using scikit-learn",
                "2. Save it as pickle to data/models/heart_disease_model.pkl",
                "3. Update HEART_DISEASE_MODEL_PATH in config.py",
                "Example training: python scripts/train_heart_disease_model.py"
            ]
        }
    
    try:
        # Prepare input features
        features = np.array([[
            age, sex, chest_pain_type, resting_bp, cholesterol,
            fasting_blood_sugar, resting_ecg, max_heart_rate,
            exercise_angina, oldpeak, slope, vessels, thal
        ]])
        
        # Make prediction
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0] if hasattr(model, 'predict_proba') else None
        
        # Calculate risk level
        risk_score = probability[1] if probability is not None else (1.0 if prediction == 1 else 0.0)
        
        if risk_score < 0.3:
            risk_level = "Low"
            recommendation = "Continue healthy lifestyle habits. Regular checkups recommended."
        elif risk_score < 0.6:
            risk_level = "Moderate"
            recommendation = "Consider lifestyle modifications. Consult with cardiologist for detailed assessment."
        else:
            risk_level = "High"
            recommendation = "Immediate consultation with cardiologist recommended. Potential for preventive interventions."
        
        return {
            "prediction": int(prediction),
            "risk_probability": float(risk_score),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "input_data": {
                "age": age,
                "sex": "Male" if sex == 1 else "Female",
                "cholesterol": cholesterol,
                "resting_bp": resting_bp,
                "max_heart_rate": max_heart_rate
            },
            "disclaimer": "This is a predictive model and should not replace professional medical advice. Always consult with a healthcare provider."
        }
        
    except Exception as e:
        logger.error(f"Heart disease prediction error: {e}")
        return {
            "error": str(e),
            "message": "Failed to generate prediction"
        }


# Example usage
if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    print("Heart Disease Prediction Tool")
    print("=" * 60)
    
    runtime = MagicMock()
    
    # Example: 55-year-old male with moderate risk factors
    result = predict_heart_disease_risk.func(
        runtime=runtime,
        age=55,
        sex=1,
        chest_pain_type=2,
        resting_bp=140,
        cholesterol=250,
        fasting_blood_sugar=1,
        resting_ecg=0,
        max_heart_rate=150,
        exercise_angina=0,
        oldpeak=1.5,
        slope=1,
        vessels=0,
        thal=2
    )
    
    print(f"\nPrediction Result:")
    if "error" in result:
        print(f"  Error: {result['error']}")
        print(f"  Message: {result['message']}")
    else:
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Risk Probability: {result['risk_probability']:.2%}")
        print(f"  Recommendation: {result['recommendation']}")
