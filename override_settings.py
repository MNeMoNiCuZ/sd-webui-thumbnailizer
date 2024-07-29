import os

def load_override_settings(override_file_path):
    override_settings = {}
    
    if not os.path.exists(override_file_path):
        create_override_settings_template(override_file_path)
        return override_settings

    with open(override_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                override_settings[key.strip()] = value.strip()

    return override_settings

def apply_override_settings(generation_set_data, override_settings):
    for key, value in override_settings.items():
        if value:  # Only override if the value is not empty
            if key in ['prompt', 'negativePrompt', 'sampler']:
                generation_set_data[key] = value
            elif key in ['steps', 'width', 'height', 'seed']:
                generation_set_data[key] = int(value)
            elif key == 'cfgScale':
                generation_set_data[key] = float(value)
            elif key.endswith('_prefix') or key.endswith('_suffix'):
                if key.startswith('prompt'):
                    base_key = 'prompt'
                elif key.startswith('negative_prompt'):
                    base_key = 'negativePrompt'
                else:
                    continue  # Skip unknown prefixes/suffixes
                
                if key.endswith('_prefix'):
                    generation_set_data[base_key] = value + ' ' + generation_set_data[base_key]
                elif key.endswith('_suffix'):
                    generation_set_data[base_key] += ' ' + value

    return generation_set_data

def create_override_settings_template(file_path):
    with open(file_path, 'w') as f:
        f.write("# Override settings for Thumbnailizer\n")
        f.write("# Leave value empty to use default from sets_user.json\n")
        f.write("prompt=\n")
        f.write("negativePrompt=\n")
        f.write("sampler=\n")
        f.write("steps=\n")
        f.write("width=\n")
        f.write("height=\n")
        f.write("cfgScale=\n")
        f.write("seed=\n")
        f.write("prompt_prefix=\n")
        f.write("prompt_suffix=\n")
        f.write("negative_prompt_prefix=\n")
        f.write("negative_prompt_suffix=\n")