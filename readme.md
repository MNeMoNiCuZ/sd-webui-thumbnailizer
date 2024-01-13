#About Thumbnailizer
Thumbnailizer is an extension for managing and generating multiple sets of thumbnails for checkpoints in Automatic1111. It allows you to switch between.

Easily switch between different sets of thumbnails to see how your checkpoints handle your preset prompts.

It's like an X/Y/Z-grid for checkpoints that you can easily update and always re-visit.

#Features
##Thumbnail Set Gallery
Switch between different sets of thumbnails for your checkpoints. Compare how all your checkpoints handle the same prompt.

##Customizable Sets
Easily edit the set list in a .JSON-file format to customize the Set dropdown menu.

##Thumbnail Set Generation
Batch generate thumbnails for each of your models based on the set file. Generation has settings for how many images to generate, and if it's allowed to override existing thumbnails.

##Customizable Blocklist
Some models are not helpful to be on sets like this. I'm looking at you v1-5-pruned! Just add it to your blocklist and it won't show up in the thumbnail gallery, and it will be ignored during thumbnail generation.

##Supports Civitai Helper Thumbnails
If you are already using the Civitai Helper-extension (https://github.com/zixaphir/Stable-Diffusion-Webui-Civitai-Helper) (forked from https://github.com/butaixianran/Stable-Diffusion-Webui-Civitai-Helper), to download your thumbnails and model info, their thumbnails are saved as modelname.preview.png. This is added to the set-list as one of the types, so you can easily switch to the original model thumbnails to view them, even if you are customizing your own sets.

#Installation
You can manually install the extension by downloading this space and placing it in your /stable-diffusion-webui/extensions-folder. To verify the folder structure afterwards, you should have a path like this: `\stable-diffusion-webui\extensions\sd-webui-thumbnailizer\scripts\`

Alternatively you can go to the Extensions-tab in A1111 and select the "Install from URL" sub-tab, and paste the URL to this extension there `https://github.com/MNeMoNiCuZ/sd-webui-thumbnailizer`. Do not forget to restart your A1111 after.

#Changelog
v0.29 - Initial release