
# Model Card — Issue Classifier

## Model

Fine-tuned DistilBERT classifier.

Base model:
distilbert-base-uncased

---

## Task

Classify GitHub issues into four maintainer triage labels:

- bug
- docs
- feature
- question

---

## Dataset

Source repository:
kubernetes/kubernetes

Label mapping:

- kind/bug → bug
- kind/documentation → docs
- kind/feature → feature
- kind/support → question

---

## Split sizes

Train: 318

Validation: 80

Test: 100

---

## Label distribution

### Train

mapped_label
bug         162
docs         91
question     48
feature      17

### Validation

mapped_label
bug         41
docs        23
question    12
feature      4

### Test

mapped_label
bug         55
question    25
docs        15
feature      5

---

## Imbalance handling

Class-weighted cross entropy was used.

Class weights:

{
  "bug": 0.49074074625968933,
  "docs": 0.8736263513565063,
  "feature": 4.676470756530762,
  "question": 1.65625
}

---

## Hyperparameters

epochs = 5

learning_rate = 2e-05

train_batch_size = 8

eval_batch_size = 16

max_length = 384

weight_decay = 0.01

warmup_steps = 20

seed = 42

---

## Test metrics

accuracy = 0.5000

macro_f1 = 0.3820

weighted_f1 = 0.5059

---

## Per-class report

              precision    recall  f1-score   support

         bug       0.75      0.49      0.59        55
        docs       0.45      0.67      0.54        15
     feature       0.00      0.00      0.00         5
    question       0.32      0.52      0.39        25

    accuracy                           0.50       100
   macro avg       0.38      0.42      0.38       100
weighted avg       0.56      0.50      0.51       100


---

## Deployment note

This model is selected because inference cost is lower than using an LLM for every request.

---

## Limitations

- Small filtered dataset
- Feature class remains underrepresented
- Label noise may exist
- Macro-F1 matters more than accuracy

---

## Artifact hashes

{
  "model.safetensors": "1272346e8a012d34965338160d0fc20d81638369405cacaf75c87de47e746a7e",
  "tokenizer_config.json": "797ed9ba72b500001971b827b0040b8743def8ec38f9cd4cda4c4945734d3596",
  "config.json": "f53e956cef60fefd7a65b94cd3859c0120ecac89185f63e34029a5244d0fb71e",
  "tokenizer.json": "c571f1b1973291370192db62060efdfb564c9a11865c568693ac7420e857cf55",
  "training_args.bin": "a40762957cc1c5cb00dab457c8d0eea9b9cafbb23f6fb3383c366aee4fc968b2"
}
