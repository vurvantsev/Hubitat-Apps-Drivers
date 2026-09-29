# Built-in source copy

The five Groovy files in this directory are the only editable Reolink sources.
`jdthomas24_sync_builtin.py` copies the app to
`driversAndApps_2.5.2/apps/src/jdthomas24/jdthomas24_ParentApp.groovy` and
the four drivers to `driversAndApps_2.5.2/devicetypes/src/jdthomas24/`,
each with a `jdthomas24_` filename prefix.
It changes the Groovy `namespace` declarations and `addChildDevice` namespace
arguments to `hubitat`. It leaves the original files and the HPM
package manifest unchanged.

From this directory, run:

```sh
python3 jdthomas24_sync_builtin.py
python3 jdthomas24_sync_builtin.py --check
```

The first command updates generated files in the sibling checkout. The second
returns a nonzero status when a copy is missing or stale, which makes it useful
for verification. The script refuses to overwrite an existing file without its
generated-file header. Review and commit changes in each repository separately.
The generated files should never be edited directly; rerun the script after
every source change.

Pass `--target /path/to/driversAndApps_2.5.2` if the checkout is elsewhere.

## On-demand upstream update

Run from this directory:

```sh
python3 jdthomas24_update_upstream.py \
  --classpath /Users/vurvantsev/hubitat/hub_2.5.1_subscriptions/build/classes/groovy/main
```

This fetches `origin` and `upstream`, switches to `main`, merges `origin/main`
and then `upstream/main`, compiles each of the five original and generated
Groovy files separately with `groovyc`, pushes `main` to your fork, and runs
`jdthomas24_sync_builtin.py` followed by its `--check` verification.
The upstream merge covers the entire fork, including integrations outside Reolink.
The command leaves the source checkout on `main`.

It requires Git authentication and `groovyc` on PATH. Tracked source changes,
unfinished Git operations, or local changes in the five generated destinations
stop the update. Unrelated target changes and untracked source files are left
alone. Git also refuses to overwrite untracked files during a checkout or merge.
Merge conflicts remain available for manual resolution; there is no automatic
reset, stash, conflict resolution, or force-push. Resolve and commit a conflict,
then rerun the command. If compilation fails, fix and commit the source first.

The built-in copies remain uncommitted for review in `driversAndApps`; commit
those generated changes before the next update. If a copy step fails after the
push, fix the destination issue and run the copy script directly, then `--check`.
Use `--target /path/to/driversAndApps_2.5.2` to override the target checkout.

Compilation uses `--classpath`, then the `CLASSPATH` environment variable, or
an automatically detected single sibling `hub_*/build/classes/groovy/main`
directory. If multiple backend builds exist, pass `--classpath` explicitly.
The classpath must provide Hubitat types such as `DuplicateDNIException`.
Compilation checks syntax and available types; it does not test hub runtime behavior.
