# classification → table training_data*
python ml/generate_data.py --samples 1000

# → ml/models/scenario_classifier.pkl
python ml/train_model.py --max-depth 7

# → ml/data/regression_training_data.json
python ml/generate_regression_data.py --samples 800

# → ml/models/regression_model.joblib
python ml/train_regression_model.py --n-estimators 100 --max-depth 10
