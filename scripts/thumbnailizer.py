# Standard library imports
import os
import sys
import shutil
import json
import glob
import threading
import configparser
from pathlib import Path
from contextlib import closing
import traceback

# Add the current directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Third party libraries, may need to be installed manually
import gradio as gr
from PIL import Image

# Automatic1111 specific imports
from modules import script_callbacks, shared, sd_models, processing, images

# Thumbnailizer script imports
from override_settings import load_override_settings, apply_override_settings, create_override_settings_template


# Pre-initialization
ckpt_dir = shared.cmd_opts.ckpt_dir or sd_models.model_path #string
script_dir = os.path.dirname(__file__) #string
user_sets_file_path = os.path.join(script_dir, 'sets_user.json') #string
user_blocklist_file_path = os.path.join(script_dir, 'blocklist_user.json') #string
# Check if sets_user.json exists, if it doesn't create it.
if not os.path.exists(user_sets_file_path):
    shutil.copy(os.path.join(script_dir, 'sets_template.json'), user_sets_file_path)
sets_file_path = os.path.join(script_dir, 'sets_user.json') #string
# Check if blocklist_user.json exists, if it doesn't create it.
if not os.path.exists(user_blocklist_file_path):
    shutil.copy(os.path.join(script_dir, 'blocklist_template.json'), user_blocklist_file_path)
model_blocklist_file_path = os.path.join(script_dir, 'blocklist_user.json') #string
if not os.path.exists(sets_file_path):
    print("Thumbnailizer Error: Unable to locate or create the sets_user.json file.")
if not os.path.exists(model_blocklist_file_path):
    print("Thumbnailizer Error: Unable to locate or create the blocklist_user.json file.")

# Load override settings
override_settings_file = os.path.join(script_dir, 'override_settings_user.txt')
if not os.path.exists(override_settings_file):
    create_override_settings_template(override_settings_file)
override_settings = load_override_settings(override_settings_file)

# Global variables
global current_set_name, current_suffix, gallery, blocked_paths, blocklist, set_data, all_model_names, all_model_paths, relevant_model_names, relevant_model_paths, data

# Configuration
current_set_name = "Default" #string
current_suffix = "" #string
blocklist = None #string
set_data = None # list of strings
all_model_names = [] #list of strings
all_model_paths = [] #list of strings
relevant_model_names = [] #list of strings
relevant_model_paths = [] #list of strings
gallery = None # Instance of gr.Gallery
gallery_height = 1000 #int
thumbnail_columns = 6 #int
gallery_fit = "contain" #str

# Load json data
def load_json_data():
    global data
    with open(sets_file_path, 'r') as file:
        data = json.load(file)

# Load settings.ini
def load_settings():
    global gallery_height, thumbnail_columns, gallery_fit
    config = configparser.ConfigParser()
    config.optionxform = str  # Keeps the case of options as is
    settings_path = os.path.join(script_dir, 'settings.ini')
    config.read(settings_path)
    # Update global variables with settings from file, if available
    gallery_height = int(config.get('Settings', 'gallery_height', fallback=gallery_height))
    thumbnail_columns = int(config.get('Settings', 'thumbnail_columns', fallback=thumbnail_columns))
    gallery_fit = str(config.get('Settings', 'gallery_fit', fallback=gallery_fit))

# Initialization function
def initialize(set_name="Default", model_blocklist_filename="blocklist_user"):
    global current_set_name, model_blocklist_file_path, blocklist, set_data, blocked_paths
    current_set_name = set_name
    model_blocklist_file_path = os.path.join(script_dir, f'{model_blocklist_filename}.json')
    load_settings()

    # Load the blocklist
    def load_model_blocklist():
        try:
            with open(model_blocklist_file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: Blocklist file not found.")
            return []
        except json.JSONDecodeError:
            print("Error: Blocklist not properly formatted.")
            return []
    blocklist = load_model_blocklist()

    # Load blocked paths
    blocked_paths_file = os.path.join(script_dir, 'blocked_paths_user.txt')
    if not os.path.exists(blocked_paths_file):
        with open(blocked_paths_file, 'w') as f:
            f.write("# List your folder paths to block here, one per line\n# True means this folder is hidden\n# False means it will be visible\n")
        blocked_paths = []
    else:
        with open(blocked_paths_file, 'r') as f:
            blocked_paths = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) == 2:
                        path, enabled = parts
                        blocked_paths.append((path, enabled.lower() == 'true'))
                    else:
                        blocked_paths.append((line, False))

    initialize_model_data()
    set_data = get_set_data(current_set_name)

# Initialize the model paths
def initialize_model_data():
    global all_model_names, all_model_paths, relevant_model_names, relevant_model_paths
    # Clear existing data
    all_model_names = []
    all_model_paths = []
    relevant_model_names = []
    relevant_model_paths = []

    # Set new data
    model_path = Path(ckpt_dir)
    model_files = glob.glob(model_path.joinpath("**/*").as_posix(), recursive=True)

    for m in model_files:
        if Path(m).suffix in {".ckpt", ".safetensors"}:
            rel_path = os.path.relpath(m, model_path.as_posix())
            all_model_names.append(Path(rel_path).name)
            all_model_paths.append(rel_path)

            # Normalize the path for comparison
            normalized_path = Path(rel_path).as_posix()

            # Check if the model is in a blocked folder path
            is_blocked = False
            for path, enabled in blocked_paths:
                if normalized_path.startswith(Path(path).as_posix()):
                    is_blocked = enabled
                if normalized_path == Path(path).as_posix() and not enabled:
                    is_blocked = False
                    break

            if rel_path not in blocklist and not is_blocked:
                relevant_model_names.append(Path(rel_path).name)
                relevant_model_paths.append(rel_path)


# Function to get the data of a specific set
def get_set_data(set_name):
    with open(sets_file_path, 'r') as file:
        data = json.load(file)
        for set_item in data["sets"]:
            if set_item["displayName"] == set_name:
                return set_item
    return None  # Return None if set not found

# Run initialization
initialize()
load_json_data()

# Function to get model thumbnail paths
def get_relevant_thumbnails(suffix=""):
    global ckpt_dir
    thumbnails = []
    missing_thumbnail_path = Path(script_dir) / "card-no-preview.png"

    for model_path in relevant_model_paths:
        model_path_obj = Path(model_path)
        model_name = model_path_obj.stem
        thumb_file = model_name + suffix + '.png' if suffix else model_name + '.png'
        thumbnail_path = Path(ckpt_dir) / model_path_obj.parent / thumb_file

        if thumbnail_path.exists():
            thumbnails.append((str(thumbnail_path), model_name))
        else:
            thumbnails.append((str(missing_thumbnail_path), model_name))

    return thumbnails

# Start thumbnail generation
def generate_thumbnails(suffix, overwrite=False, start_index=0, end_index=-1, use_override_settings=False):
    global gallery
    
    filtered_model_names = []
    filtered_model_paths = []
    generation_set_data = set_data.copy()  # Create a copy to avoid modifying the original
    print(f"--------------------------------------------------------\nThumbnailizer generation initializing for set: {current_set_name}")
    print(f"Filtering models using blocklist_user.json\n")
    
    if use_override_settings:
        override_settings = load_override_settings(override_settings_file)
        print("Using settings override:")
        for key, value in override_settings.items():
            if value:  # Only print non-empty overrides
                print(f"  {key}: {value}")
        generation_set_data = apply_override_settings(generation_set_data, override_settings)
    else:
        print("Not using settings override")

    for model_name in relevant_model_names:
        model_file_path = next((path for path in relevant_model_paths if Path(path).name == model_name), None)
        if model_file_path is None:
            print(f"Model file for {model_name} not found or blocklisted, skipping...")
            continue

        thumbnail_file_name = Path(model_name).stem + suffix + '.png'
        thumbnail_path = Path(ckpt_dir) / Path(model_file_path).parent / thumbnail_file_name

        if not overwrite and thumbnail_path.exists():
            continue

        filtered_model_names.append(model_name)
        filtered_model_paths.append(model_file_path)

    start_index = max(0, min(int(start_index), len(filtered_model_names) - 1))
    end_index = min(int(end_index), len(filtered_model_names) - 1) if int(end_index) != -1 else len(filtered_model_names) - 1
    total_to_process = (end_index - start_index) + 1

    if total_to_process == 0:
        print("No thumbnails to generate.")
        return "No thumbnails to generate."

    print(f"Generating {total_to_process} thumbnails for set: {current_set_name}")

    processed_count = 0
    for i in range(start_index, end_index + 1):
        model_name = filtered_model_names[i]
        full_model_path = os.path.join(ckpt_dir, filtered_model_paths[i])
        try:
            print(f"Generating '{current_set_name}' thumbnail for model: {model_name}\n")
            generate_thumbnail_for_model(generation_set_data, model_name, suffix, filtered_model_paths[i], full_model_path, use_override_settings)
            processed_count += 1
            print(f"Processed {processed_count}/{total_to_process} thumbnails")
        except Exception as e:
            print(f"Error generating thumbnail for {model_name}: {e}")
    
    print(f"\nThumbnailizer - Finished processing {processed_count} thumbnails")
    
    try:
        load_json_data()
        gallery_data = update_gallery(current_set_name)
        gallery.update(value=gallery_data)
    except Exception as e:
        print(f"Error updating gallery: {e}")
    
    return f"Finished processing {processed_count} thumbnails"

# Generate thumbnails for specific model (called from generate_thumbnails)
def generate_thumbnail_for_model(generation_set_data, model_name, suffix, model_path, full_model_path, use_override_settings):
    # Initialize processed to None
    processed = None
    try:
        if use_override_settings:
            print(f"Thumbnailizer: Using override settings for model: {model_name}")
            override_settings = load_override_settings(override_settings_file)
            generation_set_data = apply_override_settings(generation_set_data.copy(), override_settings)
            print(f"Thumbnailizer: Generation metadata for {model_name}:")
            for key, value in generation_set_data.items():
                print(f"  {key}: {value}")
        else:
            print(f"Thumbnailizer: Not using override settings for model: {model_name}")

        # Set up processing parameters
        p = processing.StableDiffusionProcessingTxt2Img(
            sd_model=shared.sd_model,
            prompt=generation_set_data.get("prompt", "Default Prompt"),
            negative_prompt=generation_set_data.get("negativePrompt", ""),
            steps=int(generation_set_data.get("steps", 25)),
            cfg_scale=float(generation_set_data.get("cfgScale", 6.0)),
            sampler_name=generation_set_data.get("sampler", "Default Sampler"),
            width=int(generation_set_data.get("width", 420)),
            height=int(generation_set_data.get("height", 640)),
            seed=int(generation_set_data.get("seed", -1)),
            override_settings={"sd_model_checkpoint": model_path}
        )

        # Find the full path of the model
        model_full_path = next((path for path in relevant_model_paths if Path(path).stem == Path(model_name).stem),
                               None)
        if model_full_path is None:
            raise FileNotFoundError(f"Model file for {model_name} not found or is blocklisted.")
        # Use the model's directory to save the thumbnail
        model_directory = Path(ckpt_dir) / Path(model_full_path).parent
        output_filename = f"{Path(model_name).stem}{suffix}"
        output_path = model_directory / output_filename
        # disable saving of grid
        p.do_not_save_grid = True
        # disable saving image to subdirectories
        p.override_settings['save_to_dirs'] = False
        # set image output directory
        p.outpath_samples = str(model_directory)
        # set the image filename
        p.override_settings['samples_filename_pattern'] = output_filename
        print(f"Generating thumbnail for model: {model_name} at path: {full_model_path} with output: {output_path}")
        # Perform necessary pre-processing or initialization
        p.init(["Empty Prompt"],[-1],[-1])
        # Print model info
        #print (f"\n****************************************************************************\nModel:{model_name}\nRelative Path:{model_path}\nFull Path:{full_model_path}.\n****************************************************************************\n")
        # Print set data
        #print(f"Retrieved set data for '{current_set_name}': {set_data}\n")
       
        # Process the image
        with closing(p):
            if processed is None:
                try:
                    processed = processing.process_images(p)
                except AttributeError as ae:
                    if "'NoneType' object has no attribute 'options'" in str(ae):
                        print(f"Warning: Sampler configuration issue for {model_name}. Trying with default sampler.")
                        p.sampler_name = "Euler a"  # Use a default sampler
                        processed = processing.process_images(p)
                    else:
                        raise
        # Ensure that images were generated
        if not processed or not processed.images:
            raise ValueError("No images were generated.")
        print(f"\n\nThumbnail generated and saved as {output_path}.png")
    except Exception as e:
        print(f"Error in generating thumbnail for {model_name}: {e}")
        traceback.print_exc()

# Load model paths and blocklist for the dropdown
def update_gallery(set_name):
    global current_suffix, data
    suffix = ""
    for item in data["sets"]:
        if item["displayName"] == set_name:
            suffix = item['suffix']
            if suffix:
                suffix = '.' + suffix  # Only add a period if the suffix is not empty
            break
    print(f"Thumbnailizer: Switched to set: {set_name} ({suffix})")
    current_suffix = suffix
    thumbnails = get_relevant_thumbnails(suffix)
    print(f"Thumbnailizer: Found {len(thumbnails)} relevant thumbnails")
    return [(path, name) for path, name in thumbnails]

# Functionality to generate thumbnails for all sets
def generate_thumbnails_for_all_sets(start_index=0, end_index=-1, overwrite=False, use_override_settings=False):
    global data, current_set_name, set_data
    all_thumbnails = []
    for set_item in data["sets"]:
        set_name = set_item["displayName"]
        current_set_name = set_name
        set_data = set_item
        suffix = set_item.get('suffix', '')
        if suffix:
            suffix = '.' + suffix
        print(f"Generating thumbnails for set: {set_name} with suffix: {suffix}")
        generate_thumbnails(suffix, overwrite, start_index, end_index, use_override_settings)
        all_thumbnails.extend(get_relevant_thumbnails(suffix))
    gallery.update(all_thumbnails)
    
# Thumbnailizer UI
def on_ui_tabs():
    global current_suffix, gallery, blocked_paths
    current_suffix = ''    # Initialize with empty string

    # Load choices from JSON
    with open(sets_file_path, 'r') as file:
        data = json.load(file)
    set_choices = [item["displayName"] for item in data["sets"]]
    
    # Function to save model blocklist to a file
    def save_model_blocklist(selected_models):
        with open(model_blocklist_file_path, 'w') as f:
            json.dump(selected_models, f)
        print("Thumbnailizer: Model blocklist saved to:", model_blocklist_file_path, "")
        return "Model blocklist saved!"

    with gr.Blocks(analytics_enabled=False) as ui_component:
        # Apply CSS style
        gr.Markdown(f"<link rel='stylesheet' type='text/css' href='{script_dir}/style.css'>")

        ######################## SET SETTINGS SECTION ########################
        with gr.Box(elem_classes="ch_box"):
            # Set List Dropdown
            with gr.Row():
                set_dropdown = gr.Dropdown(choices=set_choices, label="Set List", value="Default")
            # Display the path to edit the sets
            with gr.Row():
                gr.Markdown("To edit the sets, open this JSON with a text editor: `{}`".format(user_sets_file_path))

        ######################## GENERATE SECTION ########################
        with gr.Box(elem_classes="ch_box"):
            # Settings inputs
            with gr.Row():
                start_index_input = gr.Number(label="Start Index", value=0)
                last_index_input = gr.Number(label="Last Index (-1 = last index)", value=-1)
                overwrite_checkbox = gr.Checkbox(label="Overwrite Existing Thumbnails", value=False)
                use_override_settings_checkbox = gr.Checkbox(label="Use Override Settings (edit override_settings_user.txt)", value=False)

            # Generate button
            with gr.Row():
                generate_button = gr.Button("Generate Thumbnails")
                generate_all_button = gr.Button("Generate Thumbnails for All Sets")
            with gr.Row():
                generating_message = gr.Markdown()

            # Display the generation text below button
            generation_state = gr.State()

            # Add an invisible button for triggering thumbnail generation
            generate_thumbnails_button = gr.Button(visible=False)

            def display_generating_message(overwrite, start_index, end_index, use_override_settings):
                start_index = int(start_index)
                end_index = int(end_index)
                
                # Ensure we're using the current set
                current_set_name = set_dropdown.value
                initialize(current_set_name)
                
                thread = threading.Thread(target=generate_thumbnails, args=(current_suffix, overwrite, start_index, end_index, use_override_settings))
                thread.start()
                return f"Generating thumbnails for set: {current_set_name}. See console for progress. Once generated, restart A1111 or switch set back and forth to reload.", True

            def display_generating_all_message(overwrite, start_index, end_index, use_override_settings):
                start_index = int(start_index)
                end_index = int(end_index)

                thread = threading.Thread(target=generate_thumbnails_for_all_sets, args=(start_index, end_index, overwrite, use_override_settings))
                thread.start()
                return f"Generating thumbnails for all sets. See console for progress. Once generated, restart A1111 or switch set back and forth to reload.", True

            # Initiate actual generation
            def initiate_thumbnail_generation(state, overwrite, start_index, end_index, use_override_settings):
                if state:
                    generate_thumbnails(current_suffix, overwrite, start_index, end_index, use_override_settings)
                return state
            
            # Generate button action
            generate_button.click(
                fn=display_generating_message,
                inputs=[overwrite_checkbox, start_index_input, last_index_input, use_override_settings_checkbox],
                outputs=[generating_message, generation_state]
            )

            generate_all_button.click(
                fn=display_generating_all_message,
                inputs=[overwrite_checkbox, start_index_input, last_index_input, use_override_settings_checkbox],
                outputs=[generating_message, generation_state]
            )
           
            # Invisible button click event
            generate_thumbnails_button.click(
                initiate_thumbnail_generation,
                inputs=[generation_state, overwrite_checkbox, start_index_input, last_index_input, use_override_settings_checkbox],
                outputs=[]
            )

        ######################## GALLERY SECTION ########################
        with gr.Box(elem_classes="ch_box"):
            # Gallery    
            with gr.Row():
                gallery = gr.Gallery(value=get_relevant_thumbnails(current_suffix), columns=thumbnail_columns, height=gallery_height, object_fit=gallery_fit)

        ######################## BLOCKLIST SECTION ########################
        with gr.Box(elem_classes="ch_box"):
            # Load the current blocklist

            # Modify the choices to include parent folder and model name
            model_choices = [os.path.relpath(p, ckpt_dir) for p in relevant_model_paths]
            model_choices = [p for p in all_model_paths]

            # Blocklist Dropdown
            with gr.Row():
                model_list_dropdown = gr.Dropdown(label="Model Blocklist", choices=model_choices, multiselect=True, value=blocklist)
            with gr.Row():
                save_selection_button = gr.Button("Save Model Blocklist")
            with gr.Row():
                blocklist_message = gr.Markdown()

            # Function to save model blocklist and update message
            def save_model_blocklist_and_update_message(selected_models):
                global blocklist, data
                blocklist = selected_models
                with open(model_blocklist_file_path, 'w') as f:
                    json.dump(selected_models, f)
                print("Thumbnailizer: Model blocklist saved to:", model_blocklist_file_path)
                
                # Re-initialize with the new blocklist
                initialize(current_set_name)
                
                # Reload JSON data
                load_json_data()
                
                # Update the gallery
                gallery_data = update_gallery(current_set_name)
                
                message = f"Blocklist updated: {model_blocklist_file_path}"
                return message, gallery_data

            # Update the save blocklist button click event
            save_selection_button.click(
                fn=save_model_blocklist_and_update_message,
                inputs=[model_list_dropdown],
                outputs=[blocklist_message, gallery]
            )
                    
        ######################## BLOCKED PATHS SECTION ########################
        with gr.Box(elem_classes="ch_box"):
            gr.Markdown("## Blocked Paths")
            gr.Markdown(f"To edit the available blocked paths, open this file with a text editor: `{os.path.join(script_dir, 'blocked_paths_user.txt')}`")
            blocked_paths_checkboxes = gr.CheckboxGroup(
                choices=[path for path, _ in blocked_paths],
                value=[path for path, enabled in blocked_paths if enabled], label="Select which paths to block and ignore."
            )
            with gr.Row():
                update_blocked_paths_button = gr.Button("Update Blocked Paths")
            with gr.Row():
                blocked_paths_message = gr.Markdown()

        # Function to update blocked paths
        def update_blocked_paths(checkbox_values):
            global blocked_paths
            updated_paths = [(path, path in checkbox_values) for path, _ in blocked_paths]
            with open(os.path.join(script_dir, 'blocked_paths_user.txt'), 'w') as f:
                f.write("# List your folder paths to block here, one per line\n# True means this folder is hidden\n# False means it will be visible\n")
                for path, enabled in updated_paths:
                    f.write(f"{path},{enabled}\n")
            blocked_paths = updated_paths
            
            # Re-initialize model data after updating blocked paths
            initialize_model_data()
            
            # Update the gallery after changing blocked paths
            gallery_data = update_gallery(current_set_name)
            return "Blocked paths updated successfully!", gallery_data

        # Update blocked paths button
        update_blocked_paths_button.click(
            fn=update_blocked_paths,
            inputs=blocked_paths_checkboxes,
            outputs=[blocked_paths_message, gallery]
        )
        
        ######################## MISC ########################
        # Handle set changes
        def on_set_change(set_name):
            global current_set_name, set_data
            current_set_name = set_name
            set_data = get_set_data(current_set_name)
            # Re-initialize
            initialize(current_set_name)

            # Update the gallery
            gallery_data = update_gallery(set_name)
            gallery.update(gallery_data)
            return gallery_data

        # Event handling for the Set List dropdown change
        set_dropdown.change(
            fn=on_set_change,
            inputs=[set_dropdown],
            outputs=[gallery]
        )

    return [(ui_component, "Thumbnailizer", "thumbnailizer_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)

print ("Thumbnailizer initialized")