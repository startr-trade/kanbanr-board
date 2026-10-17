# Monitor release actions

When an item reaches the stage before its terminal one (for example Migration), the review queue asks which planned release it belongs to, with the planned releases as choices and 'new release' as an option. The Releases page shows each release's stage and offers 'Promote to <next stage>', with production clearly marked as the cut (tag + merge). These actions use the same commands as the CLI and need the writes-enabled monitor.
