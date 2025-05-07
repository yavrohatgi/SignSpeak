# SignSpeak: Real-Time ASL-to-Speech Glove

## Overview

**SignSpeak** is a low-cost, real-time wearable glove that allows **American Sign Language (ASL) users to communicate directly with people who do not understand ASL**. It uses **IMU sensors**, a **BeagleBone Black microcontroller**, and an **on-device machine learning model** to recognize ASL gestures and convert them into **spoken audio output**.

The glove works without any external cameras, cloud connectivity, or mobile apps—making it ideal for everyday use, emergency scenarios, and areas with limited connectivity.

---

## Why SignSpeak?

- Over **500,000 people** in the U.S. use ASL, yet **most others don’t understand it**.
- Traditional solutions like interpreters or text-based tools don’t work well in fast-paced or emergency settings.
- Existing commercial products (e.g., BrightSign Glove) cost over **$3000** and are not open source.
- SignSpeak is **affordable (~$186/unit)**, **modular**, and **open-source**—bringing sign-to-speech accessibility to everyone.

---

## Features

- **ASL Gesture Detection** using 5 IMU sensors  
- **Spoken Audio Output** via onboard amplifier + speaker  
- **Onboard ML Inference** on BeagleBone Black  
- **Battery-Powered** with ~6.85 hours continuous, ~9.6 hours standby runtime  
- **Standalone**: no phone, no internet, no camera required  

---

## Hardware Components

| Component           | Quantity | Cost    |
|--------------------|----------|---------|
| BeagleBone Black   | 1        | $53.77  |
| BMI270 IMUs        | 5        | $87.90  |
| Multiplexer        | 1        | $6.95   |
| Amplifier          | 1        | $3.95   |
| Speaker            | 1        | $3.95   |
| Battery (NiMH)     | 1        | $9.99   |
| Custom PCB         | 1        | $11.00  |
| Glove              | 1        | $5.00   |
| Misc. Components   | -        | $8.00   |
| **Total Unit Cost**| —        | **$190.51** |

---

## ML Pipeline

1. **Data**: 5 ASL signs (hello, yes, no, food, thank you), IMU-based time series  
2. **Model**: Multi-layer perceptron (MLP), trained in TensorFlow  
3. **Inference**: Model exported to `.tflite`, deployed on BeagleBone Black  
4. **Audio**: Mapped sign triggers .wav file playback via onboard speaker  

---

## Final Results

| Metric                    | Result                    |
|---------------------------|---------------------------|
| Classification Accuracy   | **93%**                   |
| Avg. Inference Time       | **0.002 sec**             |
| Audio Audibility          | **≥10 ft**                |
| Glove Weight              | **11.5 oz**               |
| Battery Life              | **6.85 hrs active**, **9.6 hrs standby** |

**Confusion Matrix Summary:**  
- Hello: 91.2% recall  
- Yes: 88% recall  
- Food: 98.2% recall  
- No: 100% recall  
- Thank You: 92.1% recall  
- **Overall F1 Score**: ~93.8%

---

## References

- [BrightSign Glove](https://www.brightsignglove.com/)
- [TensorFlow GitHub Issue #42906](https://github.com/tensorflow/tensorflow/issues/42906)
- [BMI270 IMU Datasheet](https://www.sparkfun.com/products/22398)