"""
Training Script for Cardio360-Lite STEMI Detection Model
Includes training, evaluation, quantization, and TFLite conversion
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
import tensorflow_model_optimization as tfmot
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import wandb
from datetime import datetime
import argparse
import json

from data_loader import PTBXLLoader
from resnet1d import create_resnet1d_model, SensitivityAt95Specificity, sensitivity_at_specificity

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STEMITrainer:
    """Main trainer class for STEMI detection model"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.history = None
        
        # Set random seeds for reproducibility
        tf.random.set_seed(config['seed'])
        np.random.seed(config['seed'])
        
        # Initialize Weights & Biases if enabled
        if config['use_wandb']:
            wandb.init(
                project="cardio360-lite",
                config=config,
                name=f"resnet1d_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
    
    def load_data(self):
        """Load and prepare PTB-XL dataset"""
        logger.info("Loading PTB-XL dataset...")
        
        loader = PTBXLLoader(
            data_path=self.config['data_path'],
            sampling_rate=self.config['sampling_rate']
        )
        
        self.data, self.metadata = loader.load_dataset(
            test_size=self.config['test_size'],
            val_size=self.config['val_size']
        )
        
        logger.info(f"Data loaded successfully:")
        logger.info(f"  Train: {len(self.data['X_train'])} samples")
        logger.info(f"  Validation: {len(self.data['X_val'])} samples")
        logger.info(f"  Test: {len(self.data['X_test'])} samples")
        
        # Log class distribution
        train_pos = np.sum(self.data['y_train'])
        val_pos = np.sum(self.data['y_val'])
        test_pos = np.sum(self.data['y_test'])
        
        logger.info(f"Class distribution:")
        logger.info(f"  Train STEMI: {train_pos}/{len(self.data['y_train'])} ({train_pos/len(self.data['y_train'])*100:.1f}%)")
        logger.info(f"  Val STEMI: {val_pos}/{len(self.data['y_val'])} ({val_pos/len(self.data['y_val'])*100:.1f}%)")
        logger.info(f"  Test STEMI: {test_pos}/{len(self.data['y_test'])} ({test_pos/len(self.data['y_test'])*100:.1f}%)")
    
    def create_model(self):
        """Create and compile the model"""
        logger.info("Creating ResNet1D model...")
        
        self.model = create_resnet1d_model(
            input_shape=(self.metadata['sequence_length'], self.metadata['n_leads']),
            num_classes=1,  # Binary classification
            learning_rate=self.config['learning_rate']
        )
        
        logger.info(f"Model created with {self.model.count_params():,} parameters")
        
        if self.config['verbose']:
            self.model.summary()
    
    def setup_callbacks(self):
        """Setup training callbacks"""
        callbacks = []
        
        # Early stopping
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_auc',
            patience=self.config['early_stopping_patience'],
            restore_best_weights=True,
            mode='max',
            verbose=1
        )
        callbacks.append(early_stopping)
        
        # Model checkpoint
        checkpoint_path = os.path.join(self.config['output_dir'], 'best_model.h5')
        checkpoint = keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor='val_auc',
            save_best_only=True,
            mode='max',
            verbose=1
        )
        callbacks.append(checkpoint)
        
        # Learning rate reduction
        lr_scheduler = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        )
        callbacks.append(lr_scheduler)
        
        # Custom sensitivity callback
        sensitivity_callback = SensitivityAt95Specificity(
            validation_data=(self.data['X_val'], self.data['y_val'])
        )
        callbacks.append(sensitivity_callback)
        
        # Weights & Biases callback
        if self.config['use_wandb']:
            wandb_callback = wandb.keras.WandbCallback(
                save_model=False,
                monitor='val_auc'
            )
            callbacks.append(wandb_callback)
        
        return callbacks
    
    def train(self):
        """Train the model"""
        logger.info("Starting training...")
        
        callbacks = self.setup_callbacks()
        
        self.history = self.model.fit(
            self.data['X_train'],
            self.data['y_train'],
            batch_size=self.config['batch_size'],
            epochs=self.config['epochs'],
            validation_data=(self.data['X_val'], self.data['y_val']),
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("Training completed!")
    
    def evaluate(self):
        """Evaluate the model on test set"""
        logger.info("Evaluating model on test set...")
        
        # Get predictions
        y_pred_proba = self.model.predict(self.data['X_test'])
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        test_auc = roc_auc_score(self.data['y_test'], y_pred_proba)
        sensitivity_95, threshold_95 = sensitivity_at_specificity(
            self.data['y_test'], y_pred_proba.flatten(), 0.95
        )
        
        # Classification report
        report = classification_report(
            self.data['y_test'], y_pred,
            target_names=['Non-MI', 'STEMI'],
            output_dict=True
        )
        
        # Confusion matrix
        cm = confusion_matrix(self.data['y_test'], y_pred)
        
        # Log results
        logger.info(f"Test Results:")
        logger.info(f"  AUC: {test_auc:.4f}")
        logger.info(f"  Sensitivity @ 95% Specificity: {sensitivity_95:.4f}")
        logger.info(f"  Threshold @ 95% Specificity: {threshold_95:.4f}")
        logger.info(f"  Accuracy: {report['accuracy']:.4f}")
        logger.info(f"  Precision: {report['STEMI']['precision']:.4f}")
        logger.info(f"  Recall: {report['STEMI']['recall']:.4f}")
        logger.info(f"  F1-Score: {report['STEMI']['f1-score']:.4f}")
        
        # Save results
        results = {
            'test_auc': float(test_auc),
            'sensitivity_at_95_spec': float(sensitivity_95),
            'threshold_95_spec': float(threshold_95),
            'accuracy': float(report['accuracy']),
            'precision': float(report['STEMI']['precision']),
            'recall': float(report['STEMI']['recall']),
            'f1_score': float(report['STEMI']['f1-score']),
            'confusion_matrix': cm.tolist()
        }
        
        with open(os.path.join(self.config['output_dir'], 'test_results.json'), 'w') as f:
            json.dump(results, f, indent=2)
        
        # Plot confusion matrix
        self.plot_confusion_matrix(cm)
        
        # Log to wandb
        if self.config['use_wandb']:
            wandb.log(results)
        
        return results
    
    def plot_confusion_matrix(self, cm):
        """Plot and save confusion matrix"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Non-MI', 'STEMI'],
            yticklabels=['Non-MI', 'STEMI']
        )
        plt.title('Confusion Matrix - STEMI Detection')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.config['output_dir'], 'confusion_matrix.png'), dpi=300)
        plt.close()
    
    def quantize_model(self):
        """Apply post-training quantization"""
        logger.info("Applying post-training quantization...")
        
        # Create a representative dataset for quantization
        def representative_dataset():
            for i in range(100):  # Use 100 samples for calibration
                yield [self.data['X_train'][i:i+1].astype(np.float32)]
        
        # Convert to TFLite with quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        quantized_tflite_model = converter.convert()
        
        # Save quantized model
        tflite_path = os.path.join(self.config['output_dir'], 'stemi_int8.tflite')
        with open(tflite_path, 'wb') as f:
            f.write(quantized_tflite_model)
        
        model_size_mb = len(quantized_tflite_model) / (1024 * 1024)
        logger.info(f"Quantized model saved: {tflite_path}")
        logger.info(f"Model size: {model_size_mb:.2f} MB")
        
        # Evaluate quantized model
        self.evaluate_tflite_model(tflite_path)
        
        return tflite_path
    
    def evaluate_tflite_model(self, tflite_path):
        """Evaluate TFLite quantized model"""
        logger.info("Evaluating quantized TFLite model...")
        
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Get predictions
        predictions = []
        
        for i in range(len(self.data['X_test'])):
            # Prepare input
            input_data = self.data['X_test'][i:i+1].astype(np.float32)
            
            # Quantize input if needed
            if input_details[0]['dtype'] == np.int8:
                input_scale, input_zero_point = input_details[0]['quantization']
                input_data = (input_data / input_scale + input_zero_point).astype(np.int8)
            
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            
            # Get output
            output_data = interpreter.get_tensor(output_details[0]['index'])
            
            # Dequantize output if needed
            if output_details[0]['dtype'] == np.int8:
                output_scale, output_zero_point = output_details[0]['quantization']
                output_data = (output_data.astype(np.float32) - output_zero_point) * output_scale
            
            predictions.append(output_data[0, 0])
        
        predictions = np.array(predictions)
        
        # Calculate metrics
        tflite_auc = roc_auc_score(self.data['y_test'], predictions)
        original_auc = roc_auc_score(
            self.data['y_test'], 
            self.model.predict(self.data['X_test']).flatten()
        )
        
        auc_drop = original_auc - tflite_auc
        
        logger.info(f"TFLite Model Evaluation:")
        logger.info(f"  Original AUC: {original_auc:.4f}")
        logger.info(f"  TFLite AUC: {tflite_auc:.4f}")
        logger.info(f"  AUC Drop: {auc_drop:.4f}")
        
        # Check if AUC drop is acceptable (≤ 0.02)
        if auc_drop <= 0.02:
            logger.info("✅ Quantization successful - AUC drop within acceptable range")
        else:
            logger.warning("⚠️ Quantization may have degraded performance - AUC drop > 0.02")
        
        return tflite_auc
    
    def save_model_info(self):
        """Save model metadata and configuration"""
        model_info = {
            'model_type': 'ResNet1D',
            'input_shape': [self.metadata['sequence_length'], self.metadata['n_leads']],
            'num_parameters': int(self.model.count_params()),
            'dataset': 'PTB-XL',
            'task': 'STEMI_detection',
            'config': self.config,
            'metadata': self.metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(os.path.join(self.config['output_dir'], 'model_info.json'), 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info("Model information saved")

def main():
    parser = argparse.ArgumentParser(description='Train STEMI detection model')
    parser.add_argument('--data_path', type=str, default='ptb-xl/', help='Path to PTB-XL dataset')
    parser.add_argument('--output_dir', type=str, default='outputs/', help='Output directory')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size')
    parser.add_argument('--epochs', type=int, default=30, help='Number of epochs')
    parser.add_argument('--learning_rate', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--no_wandb', action='store_true', help='Disable Weights & Biases logging')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        'data_path': args.data_path,
        'output_dir': args.output_dir,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'learning_rate': args.learning_rate,
        'early_stopping_patience': 5,
        'test_size': 0.2,
        'val_size': 0.1,
        'sampling_rate': 100,
        'seed': 42,
        'use_wandb': not args.no_wandb,
        'verbose': args.verbose
    }
    
    # Create output directory
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # Initialize trainer
    trainer = STEMITrainer(config)
    
    try:
        # Run training pipeline
        trainer.load_data()
        trainer.create_model()
        trainer.train()
        results = trainer.evaluate()
        trainer.quantize_model()
        trainer.save_model_info()
        
        logger.info("Training pipeline completed successfully!")
        
        # Check if target performance is met
        if results['test_auc'] >= 0.90:
            logger.info("🎯 Target performance achieved (AUC ≥ 0.90)!")
        else:
            logger.warning(f"⚠️ Target performance not met (AUC = {results['test_auc']:.4f} < 0.90)")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    finally:
        if config['use_wandb']:
            wandb.finish()

if __name__ == "__main__":
    main()