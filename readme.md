# About Thumbnailizer

Thumbnailizer is an extension for managing and generating multiple sets of thumbnails for checkpoints in Automatic1111.

Easily switch between different sets of thumbnails to see how your checkpoints handle your preset prompts.

It's like an X/Y/Z-grid for checkpoints that you can easily update and always re-visit.

https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/dd04d7b6-6506-4847-8405-b71925e2e6d9

# Features
## Thumbnail Set Gallery
Switch between different sets of thumbnails for your checkpoints. Compare how all your checkpoints handle the same prompt.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/20cf66b0-b2d1-4d8f-805c-268b25cc6df2)

## Customizable Sets
Easily edit the set list in a .JSON-file format to customize the Set dropdown menu.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/58d3c44c-bef0-425a-80fb-860774070559)


## Thumbnail Set Generation
Batch generate thumbnails for each of your models based on the set file. Generation has settings for how many images to generate, and if it's allowed to override existing thumbnails.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/40930bd2-6232-4e4e-803e-0b1f268731df)
_Set the [end index] to -1 to generate all missing thumbnails for a set, or check the "Overwrite" setting to re-generate all._

## Customizable Blocklist
Some models are not that useful for this. I'm looking at you v1-5-pruned! Just add it to your blocklist and it won't show up in the thumbnail gallery, and it will be ignored during thumbnail generation.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/13f5708a-d59f-4191-bd76-3cd61807bdef)
_You can use this to disable thumbnail generation for SDXL models if you want to generate them with other settings. You can manually swap between different blocklist files for now._

## Supports Civitai Helper Thumbnails
If you are already using the [Civitai Helper-extension](https://github.com/zixaphir/Stable-Diffusion-Webui-Civitai-Helper/) (forked from [this one](https://github.com/butaixianran/Stable-Diffusion-Webui-Civitai-Helper)), to download thumbnails and model info, their thumbnails are saved as modelname.preview.png. This is added to the set-list as one of the types, so you can easily switch to the original model thumbnails to view them, even if you are customizing your own sets.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/5732cc16-972f-4259-b875-d47da4f190c5)


# Installation
You can use the official extension-list and just search for "thumbnailizer":
![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/7266414e-199a-4276-bea4-880a6ed29ac1)

Alternatively you can go to the Extensions-tab in A1111 and select the "Install from URL" sub-tab, and paste the URL to this extension there `https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer`. Do not forget to restart your A1111 after.

![image](https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer/assets/60541708/d7c188ef-40c7-415e-a984-191cf52f0c51)

And lastly, you can manually install the extension by downloading this space and placing it in your /stable-diffusion-webui/extensions-folder. To verify the folder structure afterwards, you should have a path like this: `\stable-diffusion-webui\extensions\sd-webui-thumbnailizer\scripts\`

# Known Issues
>IndexError: list index out of range

The script failed to count the number of images correctly. Make sure that your Start Index and Stop Index matches the available checkpoints.

>AttributeError: 'NoneType' object has no attribute 'get'

Likely an initialization issue. Try force-refreshing your A1111, or restarting the A1111 server completely. Let it finish loading everything before using Thumbnailizer. It's sensitive.


# Changelog
v0.29 - Initial release
v0.30 - Include metadata in generated thumbnails
v0.31 - Added logic to generate a sets_user.json

# Todo / Wishlist
* Improve CSS for gallery styling, avoid the current square format, use the "cover" type to crop/fill properly
* Refresh thumbnails when a generation is done
* During generation, update a count/progress bar in the UI
* Allow switching of multiple blocklists with a drop-down
* Support other than default as the default set
* Support removal of default?
* Consider side-by-side comparison
* Verify uniqueness in sets.json
* Verify blocklist on loading and warn user about incorrect data
