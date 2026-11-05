# Custom Odoo addons

Place portfolio / custom modules in this directory. Each module must be a folder with `__init__.py` and `__manifest__.py`.

This path is mounted into the container at `/mnt/extra-addons` and is the first entry in `addons_path`.

`_addons_path_marker/` is an infrastructure-only, **non-installable** stub so Odoo 19 treats this directory as a valid addons path before real modules exist. Business modules are intentionally not implemented in the environment-setup phase.
