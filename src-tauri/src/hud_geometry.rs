use crate::model::Placement;

fn overlap(a: &Placement, b: &Placement) -> i64 {
    let w = (a.x as i64 + a.width as i64).min(b.x as i64 + b.width as i64)
        - (a.x as i64).max(b.x as i64);
    let h = (a.y as i64 + a.height as i64).min(b.y as i64 + b.height as i64)
        - (a.y as i64).max(b.y as i64);
    w.max(0) * h.max(0)
}
/// All coordinates are physical pixels in the companion's monitor work area.
/// Prefer a free side, then above/below. Clamp only to this monitor, including
/// negative origins. Attached telemetry participates in collision avoidance.
pub fn position(
    cat: &Placement,
    width: u32,
    height: u32,
    area: &Placement,
    dock: Option<&Placement>,
    gap: i32,
) -> (i32, i32) {
    let candidates = [
        (
            cat.x + cat.width as i32 + gap,
            cat.y + (cat.height as i32 - height as i32) / 2,
        ),
        (
            cat.x - width as i32 - gap,
            cat.y + (cat.height as i32 - height as i32) / 2,
        ),
        (
            cat.x + (cat.width as i32 - width as i32) / 2,
            cat.y - height as i32 - gap,
        ),
        (
            cat.x + (cat.width as i32 - width as i32) / 2,
            cat.y + cat.height as i32 + gap,
        ),
    ];
    candidates
        .into_iter()
        .map(|(x, y)| {
            let x = x.clamp(
                area.x,
                (area.x + area.width as i32 - width as i32).max(area.x),
            );
            let y = y.clamp(
                area.y,
                (area.y + area.height as i32 - height as i32).max(area.y),
            );
            let rect = Placement {
                x,
                y,
                width,
                height,
            };
            (
                overlap(&rect, cat) * 10 + dock.map_or(0, |d| overlap(&rect, d)),
                x,
                y,
            )
        })
        .min_by_key(|(score, _, _)| *score)
        .map(|(_, x, y)| (x, y))
        .unwrap()
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn corners_negative_origins_and_scaled_sizes_stay_inside_work_area() {
        for scale in [1., 1.25, 1.5, 2.] {
            let area = Placement {
                x: -1920,
                y: -200,
                width: 1920,
                height: 1040,
            };
            let size = (240. * scale) as u32;
            let width = (248. * scale) as u32;
            let height = (136. * scale) as u32;
            for (x, y) in [
                (-1920, -200),
                (-1920, 840 - (size as i32)),
                (-(size as i32), -200),
                (-(size as i32), 840 - (size as i32)),
            ] {
                let cat = Placement {
                    x,
                    y,
                    width: size,
                    height: size,
                };
                let (x, y) = position(&cat, width, height, &area, None, (12. * scale) as i32);
                let hud = Placement {
                    x,
                    y,
                    width,
                    height,
                };
                assert_eq!(overlap(&cat, &hud), 0);
                assert!(
                    x >= area.x && y >= area.y && x + width as i32 <= 0 && y + height as i32 <= 840
                );
            }
        }
    }
    #[test]
    fn attached_dock_is_avoided_when_another_side_is_free() {
        let area = Placement {
            x: 0,
            y: 0,
            width: 1920,
            height: 1040,
        };
        let cat = Placement {
            x: 1550,
            y: 700,
            width: 300,
            height: 300,
        };
        let dock = Placement {
            x: 1075,
            y: 350,
            width: 460,
            height: 650,
        };
        let (x, y) = position(&cat, 310, 170, &area, Some(&dock), 15);
        let hud = Placement {
            x,
            y,
            width: 310,
            height: 170,
        };
        assert_eq!(overlap(&cat, &hud) + overlap(&dock, &hud), 0);
    }
}
