"""
1D ResNet-18 Implementation for ECG Classification
Adapted for 12-channel ECG data and STEMI detection
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from typing import Tuple

class ResidualBlock1D(layers.Layer):
    """1D Residual Block for ECG signals"""
    
    def __init__(self, filters: int, kernel_size: int = 3, stride: int = 1, **kwargs):
        super(ResidualBlock1D, self).__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        self.stride = stride
        
        # First convolutional layer
        self.conv1 = layers.Conv1D(
            filters=filters,
            kernel_size=kernel_size,
            strides=stride,
            padding='same',
            use_bias=False
        )
        self.bn1 = layers.BatchNormalization()
        
        # Second convolutional layer
        self.conv2 = layers.Conv1D(
            filters=filters,
            kernel_size=kernel_size,
            strides=1,
            padding='same',
            use_bias=False
        )
        self.bn2 = layers.BatchNormalization()
        
        # Shortcut connection
        if stride != 1:
            self.shortcut = keras.Sequential([
                layers.Conv1D(filters, 1, strides=stride, use_bias=False),
                layers.BatchNormalization()
            ])
        else:
            self.shortcut = lambda x: x
        
        self.relu = layers.ReLU()
    
    def call(self, inputs, training=None):
        # Main path
        x = self.conv1(inputs)
        x = self.bn1(x, training=training)
        x = self.relu(x)
        
        x = self.conv2(x)
        x = self.bn2(x, training=training)
        
        # Shortcut path
        shortcut = self.shortcut(inputs)
        
        # Add shortcut and apply ReLU
        x = layers.add([x, shortcut])
        x = self.relu(x)
        
        return x

class ResNet1D(keras.Model):
    """1D ResNet-18 for ECG Classification"""
    
    def __init__(self, num_classes: int = 1, input_shape: Tuple[int, int] = (1000, 12), **kwargs):
        super(ResNet1D, self).__init__(**kwargs)
        
        self.num_classes = num_classes
        self.input_shape_custom = input_shape
        
        # Initial convolution
        self.conv1 = layers.Conv1D(
            filters=64,
            kernel_size=7,
            strides=2,
            padding='same',
            use_bias=False
        )
        self.bn1 = layers.BatchNormalization()
        self.relu = layers.ReLU()
        self.maxpool = layers.MaxPooling1D(pool_size=3, strides=2, padding='same')
        
        # Residual blocks (ResNet-18 architecture)
        # Layer 1: 2 blocks, 64 filters
        self.layer1_block1 = ResidualBlock1D(64, stride=1)
        self.layer1_block2 = ResidualBlock1D(64, stride=1)
        
        # Layer 2: 2 blocks, 128 filters
        self.layer2_block1 = ResidualBlock1D(128, stride=2)
        self.layer2_block2 = ResidualBlock1D(128, stride=1)
        
        # Layer 3: 2 blocks, 256 filters
        self.layer3_block1 = ResidualBlock1D(256, stride=2)
        self.layer3_block2 = ResidualBlock1D(256, stride=1)
        
        # Layer 4: 2 blocks, 512 filters
        self.layer4_block1 = ResidualBlock1D(512, stride=2)
        self.layer4_block2 = ResidualBlock1D(512, stride=1)
        
        # Global average pooling and classifier
        self.global_avgpool = layers.GlobalAveragePooling1D()
        self.dropout = layers.Dropout(0.3)
        
        # Binary classification (STEMI vs non-MI)
        if num_classes == 1:
            self.classifier = layers.Dense(1, activation='sigmoid', name='predictions')
        else:
            self.classifier = layers.Dense(num_classes, activation='softmax', name='predictions')
    
    def call(self, inputs, training=None):
        # Initial convolution
        x = self.conv1(inputs)
        x = self.bn1(x, training=training)
        x = self.relu(x)
        x = self.maxpool(x)
        
        # Residual blocks
        x = self.layer1_block1(x, training=training)
        x = self.layer1_block2(x, training=training)
        
        x = self.layer2_block1(x, training=training)
        x = self.layer2_block2(x, training=training)
        
        x = self.layer3_block1(x, training=training)
        x = self.layer3_block2(x, training=training)
        
        x = self.layer4_block1(x, training=training)
        x = self.layer4_block2(x, training=training)
        
        # Global pooling and classification
        x = self.global_avgpool(x)
        x = self.dropout(x, training=training)
        x = self.classifier(x)
        
        return x
    
    def build_model(self):
        """Build the model with specified input shape"""
        inputs = keras.Input(shape=self.input_shape_custom)
        outputs = self.call(inputs)
        return keras.Model(inputs, outputs, name='ResNet1D_ECG')

class FocalLoss(keras.losses.Loss):
    """Focal Loss for handling class imbalance in STEMI detection"""
    
    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):
        super(FocalLoss, self).__init__(**kwargs)
        self.alpha = alpha
        self.gamma = gamma
    
    def call(self, y_true, y_pred):
        # Compute focal loss
        epsilon = tf.keras.backend.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
        
        # Compute cross entropy
        ce = -y_true * tf.math.log(y_pred) - (1 - y_true) * tf.math.log(1 - y_pred)
        
        # Compute focal weight
        alpha_t = y_true * self.alpha + (1 - y_true) * (1 - self.alpha)
        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        focal_weight = alpha_t * tf.pow(1 - p_t, self.gamma)
        
        # Apply focal weight
        focal_loss = focal_weight * ce
        
        return tf.reduce_mean(focal_loss)

def create_resnet1d_model(
    input_shape: Tuple[int, int] = (1000, 12),
    num_classes: int = 1,
    learning_rate: float = 1e-3
) -> keras.Model:
    """
    Create and compile ResNet1D model for ECG classification
    
    Args:
        input_shape: Input shape (sequence_length, n_channels)
        num_classes: Number of output classes (1 for binary)
        learning_rate: Learning rate for optimizer
        
    Returns:
        Compiled Keras model
    """
    # Create model
    resnet = ResNet1D(num_classes=num_classes, input_shape=input_shape)
    model = resnet.build_model()
    
    # Compile model
    optimizer = keras.optimizers.AdamW(learning_rate=learning_rate)
    
    if num_classes == 1:
        # Binary classification
        loss = FocalLoss(alpha=0.25, gamma=2.0)
        metrics = [
            'binary_accuracy',
            keras.metrics.AUC(name='auc'),
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall')
        ]
    else:
        # Multi-class classification
        loss = 'sparse_categorical_crossentropy'
        metrics = ['accuracy']
    
    model.compile(
        optimizer=optimizer,
        loss=loss,
        metrics=metrics
    )
    
    return model

def sensitivity_at_specificity(y_true, y_pred, specificity=0.95):
    """Calculate sensitivity at given specificity"""
    from sklearn.metrics import roc_curve
    
    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    
    # Find threshold for desired specificity
    target_fpr = 1 - specificity
    idx = np.argmin(np.abs(fpr - target_fpr))
    
    return tpr[idx], thresholds[idx]

# Custom callback for sensitivity at 95% specificity
class SensitivityAt95Specificity(keras.callbacks.Callback):
    """Callback to monitor sensitivity at 95% specificity"""
    
    def __init__(self, validation_data):
        super().__init__()
        self.validation_data = validation_data
    
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        
        # Get validation predictions
        val_x, val_y = self.validation_data
        val_pred = self.model.predict(val_x, verbose=0)
        
        # Calculate sensitivity at 95% specificity
        sensitivity, threshold = sensitivity_at_specificity(val_y, val_pred.flatten(), 0.95)
        
        logs['val_sensitivity_at_95_spec'] = sensitivity
        logs['val_threshold_95_spec'] = threshold
        
        print(f" - val_sensitivity_at_95_spec: {sensitivity:.4f}")

if __name__ == "__main__":
    # Test model creation
    model = create_resnet1d_model()
    model.summary()
    
    # Test with dummy data
    dummy_input = tf.random.normal((32, 1000, 12))
    dummy_output = model(dummy_input)
    print(f"Output shape: {dummy_output.shape}")
    
    # Count parameters
    total_params = model.count_params()
    print(f"Total parameters: {total_params:,}")
    
    # Estimate model size (rough approximation)
    model_size_mb = (total_params * 4) / (1024 * 1024)  # 4 bytes per float32 parameter
    print(f"Estimated model size: {model_size_mb:.1f} MB")