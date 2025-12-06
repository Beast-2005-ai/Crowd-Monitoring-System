from ultralytics import YOLO

def main():
    """
    This script downloads an official pre-trained YOLOv8 model,
    quantizes it to FP16 (half-precision), and exports it to the ONNX format.
    This creates a smaller, faster model ideal for edge devices like the Raspberry Pi.
    """
    
    model_version = 'yolov8n.pt'
    
    # 1. Load the official pre-trained YOLOv8n model.
    print(f"Loading the official pre-trained model: {model_version}...")
    try:
        model = YOLO(model_version)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model. Please check your internet connection. Details: {e}")
        return

    # 2. Export the model to ONNX format with FP16 (half-precision) quantization.
    print("\nStarting FP16 quantization process. This may take a moment...")
    try:
        # --- THIS IS THE CORRECTED LINE ---
        # The 'int8=True' argument is deprecated for ONNX.
        # We now use 'half=True' for FP16 quantization, which is the modern standard.
        model.export(
            format='onnx',
            half=True,       # The key flag to enable FP16 (half-precision) quantization
            simplify=True    # Simplifies the ONNX graph for better performance
        )
        # --------------------------------

        print("\nQuantization and export complete!")
        
        # The exported file will typically be in a new 'runs' directory.
        print(f"A new FP16 quantized file named '{model_version.replace('.pt', '.onnx')}' has been created.")
        print("You can find it in a new subfolder, usually named 'runs/detect/export/'.")

    except Exception as e:
        print(f"An error occurred during export/quantization: {e}")


if __name__ == '__main__':
    main()

