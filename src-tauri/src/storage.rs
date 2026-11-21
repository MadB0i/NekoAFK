use crate::model::Config;
use sha2::{Digest, Sha256};
use std::{fs, io::Read, path::Path};

pub fn save(dir: &Path, config: &Config) -> Result<(), String> {
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    let tmp = dir.join("settings.json.tmp");
    let bytes = serde_json::to_vec_pretty(config).map_err(|e| e.to_string())?;
    let mut file = fs::File::create(&tmp).map_err(|e| e.to_string())?;
    std::io::Write::write_all(&mut file, &bytes).map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())?;
    drop(file);
    fs::rename(tmp, dir.join("settings.json")).map_err(|e| e.to_string())
}
pub fn load(dir: &Path) -> (Config, Option<String>) {
    let file = dir.join("settings.json");
    match fs::read(&file) {
        Ok(bytes) => match serde_json::from_slice::<Config>(&bytes) {
            Ok(c) if c.settings.validate_structure().is_ok() => {
                let notice = if !c.settings.workspace.is_empty()
                    && !Path::new(&c.settings.workspace).is_dir()
                {
                    Some("Saved workspace is unavailable. Choose an existing folder before verifying.".into())
                } else {
                    None
                };
                (c, notice)
            }
            _ => {
                let backup = dir.join(format!("settings.corrupt-{}.json", crate::model::now()));
                let preserved = fs::rename(file, backup).is_ok();
                (Config::default(), Some(if preserved { "Invalid settings preserved in a settings.corrupt file. Defaults restored." } else { "Settings could not be read or backed up. Check the data folder permissions." }.into()))
            }
        },
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (Config::default(), None),
        Err(_) => (
            Config::default(),
            Some("Settings could not be read. Check the data folder permissions.".into()),
        ),
    }
}
pub fn same_workspace(a: &str, b: &str) -> bool {
    match (fs::canonicalize(a), fs::canonicalize(b)) {
        (Ok(a), Ok(b)) => a
            .to_string_lossy()
            .eq_ignore_ascii_case(&b.to_string_lossy()),
        _ => false,
    }
}

// Ignore generated/dependency/archive folders, then hash actual source bytes.
pub fn fingerprint(root: &Path) -> Result<Vec<u8>, String> {
    fn walk(
        dir: &Path,
        root: &Path,
        hash: &mut Sha256,
        count: &mut u64,
        bytes: &mut u64,
    ) -> Result<(), String> {
        let mut files = fs::read_dir(dir)
            .map_err(|_| "Cannot read workspace during verification")?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|_| "Cannot inspect workspace")?;
        files.sort_by_key(|e| e.file_name());
        for e in files {
            let name = e.file_name();
            let name = name.to_string_lossy();
            if [
                ".git",
                "node_modules",
                "target",
                "dist",
                "archive",
                ".artifacts",
                ".opencode",
                "__pycache__",
                ".venv",
            ]
            .contains(&name.as_ref())
            {
                continue;
            }
            let ty = e
                .file_type()
                .map_err(|_| "Cannot inspect workspace entry")?;
            if ty.is_symlink() {
                return Err("Source symlink cannot be independently fingerprinted".into());
            }
            if ty.is_dir() {
                walk(&e.path(), root, hash, count, bytes)?;
            } else if ty.is_file() {
                *count += 1;
                if *count > 20000 {
                    return Err("Workspace has too many source files for safe verification".into());
                }
                hash.update(
                    e.path()
                        .strip_prefix(root)
                        .map_err(|_| "Invalid workspace path")?
                        .to_string_lossy()
                        .as_bytes(),
                );
                hash.update([0]);
                let mut file = fs::File::open(e.path()).map_err(|_| "Cannot read source file")?;
                let mut buffer = [0u8; 65536];
                loop {
                    let n = file
                        .read(&mut buffer)
                        .map_err(|_| "Cannot fingerprint source file")?;
                    if n == 0 {
                        break;
                    }
                    *bytes += n as u64;
                    if *bytes > 256 * 1024 * 1024 {
                        return Err("Source exceeds the verification fingerprint budget; choose a narrower workspace".into());
                    }
                    hash.update(&buffer[..n]);
                }
                hash.update([0]);
            }
        }
        Ok(())
    }
    let mut hash = Sha256::new();
    walk(root, root, &mut hash, &mut 0, &mut 0)?;
    Ok(hash.finalize().to_vec())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn saved_preferences_are_validated_without_discarding_an_unavailable_workspace() {
        let d = tempfile::tempdir().unwrap();
        let mut c = Config::default();
        c.settings.workspace = d.path().join("missing-workspace").to_string_lossy().into();
        save(d.path(), &c).unwrap();
        let (loaded, notice) = load(d.path());
        assert_eq!(loaded.settings.workspace, c.settings.workspace);
        assert!(notice.is_some());
        c.settings.personality = "invalid".into();
        save(d.path(), &c).unwrap();
        let (loaded, notice) = load(d.path());
        assert_eq!(loaded.settings.personality, "playful");
        assert!(notice.is_some());
        c.settings.character = "invalid".into();
        save(d.path(), &c).unwrap();
        let (loaded, notice) = load(d.path());
        assert_eq!(loaded.settings.character, "robot");
        assert!(notice.is_some());
    }
    #[test]
    fn settings_replace_and_corruption_is_preserved() {
        let d = tempfile::tempdir().unwrap();
        let mut c = Config::default();
        save(d.path(), &c).unwrap();
        c.settings.scale = 1.5;
        save(d.path(), &c).unwrap();
        assert_eq!(load(d.path()).0.settings.scale, 1.5);
        fs::write(d.path().join("settings.json"), b"bad json").unwrap();
        assert!(load(d.path()).1.is_some());
        assert!(fs::read_dir(d.path()).unwrap().any(|e| e
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with("settings.corrupt")));
    }
    #[test]
    fn fingerprint_catches_same_length_edits() {
        let d = tempfile::tempdir().unwrap();
        fs::write(d.path().join("source.txt"), "abc").unwrap();
        let a = fingerprint(d.path()).unwrap();
        fs::write(d.path().join("source.txt"), "xyz").unwrap();
        assert_ne!(a, fingerprint(d.path()).unwrap());
    }
}
