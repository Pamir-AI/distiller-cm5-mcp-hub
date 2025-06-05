import io
from picamera2 import Picamera2
from PIL import Image, ImageDraw, ImageFont
import datetime

def capture_snapshot() -> bytes:
    """
    Captures a single JPEG image from the Pi Camera and returns it as raw bytes.
    If no camera is available, generates a test image.
    """
    picam = None
    try:
        # Check if cameras are available
        available_cameras = Picamera2.global_camera_info()
        if not available_cameras:
            print("No cameras detected, generating test image...")
            return generate_test_image()
        
        picam = Picamera2()
        picam.configure(picam.create_still_configuration())
        picam.start()
        
        # Capture directly to memory buffer instead of file
        stream = io.BytesIO()
        picam.capture_file(stream, format='jpeg')
        
        # Get the image bytes
        stream.seek(0)
        img_bytes = stream.read()
        return img_bytes
        
    except Exception as e:
        print(f"Camera capture failed: {e}, generating test image...")
        return generate_test_image()
    finally:
        # Ensure camera is always properly closed
        if picam is not None:
            try:
                picam.stop()
                picam.close()
            except Exception as e:
                print(f"Error closing camera: {e}")

def generate_test_image() -> bytes:
    """
    Generate a test image when no camera is available.
    """
    # Create a test image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(image)
    
    # Add some text
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_lines = [
        "Pi Camera MCP Server",
        "Test Image Mode",
        f"Generated: {timestamp}",
        "",
        "No camera detected",
        "This is a demo image"
    ]
    
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    y_offset = 50
    for line in text_lines:
        if font:
            draw.text((50, y_offset), line, fill='darkblue', font=font)
        else:
            draw.text((50, y_offset), line, fill='darkblue')
        y_offset += 40
    
    # Draw a simple pattern
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill='lightgray', width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill='lightgray', width=1)
    
    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=95)
    output.seek(0)
    return output.read()



if __name__ == "__main__":
    img_bytes = capture_snapshot()
    # save to file for debug 
    with open("test_image.jpg", "wb") as f:
        f.write(img_bytes) 