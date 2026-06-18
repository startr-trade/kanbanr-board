# config rename-status (P1)

Renaming a status shouldn't require re-specifying the whole workflow. One command renames it everywhere (statuses, displayed/no-op, default, transitions) AND migrates the feature items in it (on-disk `<status>/` folder + each feature's status).