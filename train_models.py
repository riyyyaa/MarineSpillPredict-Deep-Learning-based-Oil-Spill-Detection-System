import os
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

def build_unet(input_shape=(256, 256, 3)):
    inputs = Input(input_shape)
    
    # Downsample
    c1 = Conv2D(16, (3, 3), activation='relu', padding='same')(inputs)
    p1 = MaxPooling2D((2, 2))(c1)
    
    # Bottleneck
    c2 = Conv2D(32, (3, 3), activation='relu', padding='same')(p1)
    
    # Upsample
    u3 = UpSampling2D((2, 2))(c2)
    c3 = concatenate([u3, c1])
    c3 = Conv2D(16, (3, 3), activation='relu', padding='same')(c3)
    
    outputs = Conv2D(1, (1, 1), activation='sigmoid')(c3)
    
    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def build_deeplab_dummy():
    # A simple proxy to represent a DeepLab stub
    return build_unet()

if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    unet_path = os.path.join(MODEL_DIR, "unet.h5")
    deeplab_path = os.path.join(MODEL_DIR, "deeplab.h5")
    
    print("Building Untrained UNet model...")
    unet = build_unet()
    unet.save(unet_path)
    print(f"Saved {unet_path}")
    
    print("Building Untrained DeepLabV3 model...")
    deeplab = build_deeplab_dummy()
    deeplab.save(deeplab_path)
    print(f"Saved {deeplab_path}")
    
    print("Models created! You can now run the backend without missing model errors.")
