backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── raspberry_pi.py
│   │   ├── device.py
│   │   ├── presence.py
│   │   ├── light_reading.py
│   │   ├── event.py
│   │   ├── rule.py
│   │   ├── training_data.py
│   │   ├── smart_dimming_adjustment.py
│   │   └── user_preference.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── device.py
│   │   ├── rule.py
│   │   ├── smart_dimming.py
│   │   ├── event.py
│   │   └── raspberry_pi.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── devices.py
│   │   ├── events.py
│   │   ├── rules.py
│   │   ├── ai.py
│   │   ├── smart_dimming.py
│   │   └── raspberry_pis.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── device_service.py
│   │   ├── rule_engine.py
│   │   ├── ai_service.py
│   │   └── smart_dimming_service.py
│   └── utils/
│       ├── __init__.py
│       ├── auth.py
│       └── validators.py
├── ml/
│   ├── __init__.py
│   ├── train_model.py
│   ├── generate_data.py
│   └── models/
│       └── .gitkeep
├── requirements.txt
├── .env.example
└── README.md

