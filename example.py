"""
Example usage of the Minute Mail
"""

from minute_mail import MinuteMail
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def example_basic_usage():
    """
    Basic example: Scan a single mail image
    """
    print("=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)

    # Create scanner (automatically uses Gemini if GEMINI_API_KEY is set)
    scanner = MinuteMail()

    # Scan a mail image
    image_path = "sample_mail.jpg"  # Replace with your image path

    if not os.path.exists(image_path):
        print(f"Note: Sample image '{image_path}' not found.")
        print("Please provide a path to a mail image to test.")
        return

    result = scanner.scan_mail(image_path)

    # Display results
    print(f"\nMethod used: {result['method']}")
    print(f"Sender Name: {result['sender_name']}")
    print(f"Street: {result['street']}")
    print(f"City: {result['city']}")
    print(f"State: {result['state']}")
    print(f"ZIP: {result['zip']}")
    print(f"Full Address: {result['full_address']}")
    print()


def example_batch_processing():
    """
    Example: Process multiple mail images
    """
    print("=" * 60)
    print("EXAMPLE 2: Batch Processing")
    print("=" * 60)

    scanner = MinuteMail()

    # List of mail images to process
    image_paths = [
        "mail_1.jpg",
        "mail_2.jpg",
        "mail_3.jpg"
    ]

    results = []
    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"Skipping {image_path} - file not found")
            continue

        print(f"\nProcessing: {image_path}")
        result = scanner.scan_mail(image_path)
        results.append({
            'image': image_path,
            'data': result
        })
        print(f"  Sender: {result['sender_name']}")
        print(f"  Address: {result['full_address']}")

    print(f"\nProcessed {len(results)} images")
    print()


def example_explicit_api_key():
    """
    Example: Explicitly provide API key instead of using environment variable
    """
    print("=" * 60)
    print("EXAMPLE 3: Explicit API Key")
    print("=" * 60)

    # Option 1: Pass API key directly
    api_key = "your_api_key_here"  # Replace with actual key
    scanner = MinuteMail(gemini_api_key=api_key)

    # Option 2: Use environment variable (recommended)
    # scanner = MinuteMail()  # Reads from GEMINI_API_KEY env var

    print("Scanner initialized with explicit API key")
    print()


def example_force_tesseract():
    """
    Example: Force using Tesseract instead of Gemini
    """
    print("=" * 60)
    print("EXAMPLE 4: Force Tesseract OCR")
    print("=" * 60)

    # Force Tesseract usage (useful for offline processing or testing)
    scanner = MinuteMail(use_gemini=False)

    image_path = "sample_mail.jpg"

    if not os.path.exists(image_path):
        print(f"Note: Sample image '{image_path}' not found.")
        return

    result = scanner.scan_mail(image_path)
    print(f"Method used: {result['method']}")
    print(f"Result: {result}")
    print()


def example_with_error_handling():
    """
    Example: Proper error handling
    """
    print("=" * 60)
    print("EXAMPLE 5: With Error Handling")
    print("=" * 60)

    scanner = MinuteMail()
    image_path = "sample_mail.jpg"

    try:
        result = scanner.scan_mail(image_path)

        if result['sender_name'] or result['full_address']:
            print("Successfully extracted mail information:")
            print(f"  Sender: {result['sender_name']}")
            print(f"  Address: {result['full_address']}")
        else:
            print("Warning: No information could be extracted from the image")

    except FileNotFoundError:
        print(f"Error: Image file not found: {image_path}")
    except Exception as e:
        print(f"Error processing mail: {e}")

    print()


def main():
    """
    Run all examples
    """
    print("\n" + "=" * 60)
    print("MINUTE MAIL - EXAMPLES")
    print("=" * 60 + "\n")

    # Check if API key is configured
    if not os.getenv('GEMINI_API_KEY'):
        print("WARNING: GEMINI_API_KEY not found in environment variables")
        print("Please set it in your .env file or export it:")
        print("  export GEMINI_API_KEY='your_api_key_here'\n")

    # Run examples
    example_basic_usage()
    # example_batch_processing()  # Uncomment to run
    # example_explicit_api_key()  # Uncomment to run
    # example_force_tesseract()   # Uncomment to run
    # example_with_error_handling()  # Uncomment to run

    print("\n" + "=" * 60)
    print("TIP: Edit this file to uncomment more examples")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
