from PIL import Image, ImageOps
import os

def convert_4bit_to_8bit(data):
    """Converts 4-bit grayscale data to 8-bit."""
    xs = bytearray()
    for byte in data:
        high = (byte >> 4) & 0xF
        low = byte & 0xF
        high *= 16
        low *= 16
        xs.extend(high.to_bytes(1, 'big'))
        xs.extend(low.to_bytes(1, 'big'))
    return xs

def extract_image_from_record(data, output_path, width=120, height=120, offset=36):
    """Extracts and saves the image from a single record."""
    try:
        image_data = convert_4bit_to_8bit(data[offset:])
        if len(image_data) < width * height:
            return  # Suppress error message for insufficient data
        
        img = Image.frombytes("L", (width, height), bytes(image_data[:width * height]))
        img_invert = ImageOps.invert(img)
        
        img_invert.save(output_path)
        print(f"Image saved: {output_path}")
    except Exception as e:
        pass  # Suppress additional error messages

def parse_pdb_records(pdb_data):
    """Parse the PDB file to determine record offsets."""
    record_offsets = []
    header_size = 78
    record_entry_size = 8
    num_records = int.from_bytes(pdb_data[76:78], byteorder='big')
    
    offset_table_start = header_size
    for i in range(num_records):
        record_offset = int.from_bytes(
            pdb_data[offset_table_start + (i * record_entry_size): offset_table_start + (i * record_entry_size) + 4], 
            byteorder='big'
        )
        record_offsets.append(record_offset)
    
    return record_offsets

def is_valid_image_data(data, width, height, offset=36):
    """Check if the record contains enough data for a valid image."""
    expected_length = (width * height) // 2 + offset  # 4-bit data means each pixel is half a byte
    return len(data) >= expected_length

def process_pdb_file(pdb_path, output_dir, width=120, height=120):
    """Process the PDB file to extract images from each record."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(pdb_path, "rb") as pdb_file:
            pdb_data = pdb_file.read()
        
        # Parse the PDB file to get actual record offsets
        record_offsets = parse_pdb_records(pdb_data)
        
        # Extract images based on parsed offsets
        for idx, start_offset in enumerate(record_offsets):
            end_offset = record_offsets[idx + 1] if idx + 1 < len(record_offsets) else len(pdb_data)
            record_data = pdb_data[start_offset:end_offset]
            
            if not is_valid_image_data(record_data, width, height, offset=36):
                continue  # Suppress message for invalid image data
            
            output_path = os.path.join(output_dir, f"image_{idx}.png")
            extract_image_from_record(record_data, output_path, width, height, offset=36)
    
    except FileNotFoundError:
        print(f"PDB file not found: {pdb_path}")
    except Exception as e:
        pass  # Suppress additional error messages

# Assuming the PDB file is located in the `pdb` directory:
pdb_file_path = "pdb/wqvlinkdb.pdb"
output_images_dir = "out"

# Process the PDB file
process_pdb_file(pdb_file_path, output_images_dir)
