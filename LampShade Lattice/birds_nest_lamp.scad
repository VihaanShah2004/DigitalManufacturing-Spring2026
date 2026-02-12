// ═══════════════════════════════════════════════════════════════
//  BIRD'S NEST CAGE LAMP  —  Table Lamp Version
//
//  A hollow sphere built entirely from crossing cylindrical rods.
//  Every rod connects two grid nodes → nothing floats.
//
//  Strategy:
//   ① Build a (rows × cols) grid of nodes on an oblate spheroid.
//   ② Apply seeded random offsets to make it look organic/chaotic.
//   ③ Connect nodes with hull()-capsule rods using 5 connection
//      patterns per cell (meridional, latitudinal, two diagonals,
//      one long skip-diagonal).
//   ④ Fan all top-row nodes to a single apex → closed top.
//   ⑤ Connect bottom row to a solid base ring → stable on table.
//   ⑥ Punch bottom opening for light/socket.
// ═══════════════════════════════════════════════════════════════

$fn = 7;          // facets on hull-sphere endcaps  (raise to 12 for final render)
$fa = 6;
$fs = 1.5;

/* ── SHELL SHAPE ─────────────────────────────────────── */
outer_r  = 40;    // sphere radius (mm)
z_scale  = 1;  // vertical squash  (1 = sphere)

/* ── ROD STYLE ───────────────────────────────────────── */
rod_r    = 0.7;   // rod cross-section radius (mm)
node_r   = rod_r + 0.4; // slightly larger sphere at each hull-cap end

/* ── GRID ────────────────────────────────────────────── */
rows     = 9;     // latitude rings (excluding apex)
cols     = 13;    // longitude columns
theta_lo = 22;    // polar angle at top row   (deg from +Z)
theta_hi = 158;   // polar angle at bottom row

/* ── ORGANIC PERTURBATION ────────────────────────────── */
perturb  = 3.5;   // ± max random offset per node (mm)
seed     = 137;   // change to get a different "nest"

/* ── OPENINGS ────────────────────────────────────────── */
base_ring_r   = 18;  // inner radius of base ring (sits on table)
base_ring_w   =  5;  // width of base ring cross-section
base_ring_h   =  5;  // height of base ring
bottom_cut_r  = 17;  // hole punched at the bottom for light
top_hub_r     =  3;  // solid hub sphere at apex

// ─────────────────────────────────────────────────────────────
//  PRE-COMPUTE RANDOM OFFSETS
//  rands(min, max, n, seed)  →  n uniform values
// ─────────────────────────────────────────────────────────────
total_pts = rows * cols;
rx = rands(-perturb, perturb, total_pts, seed + 0);
ry = rands(-perturb, perturb, total_pts, seed + 1);
rz = rands(-perturb * 0.6, perturb * 0.6, total_pts, seed + 2);

// ─────────────────────────────────────────────────────────────
//  HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────

function theta_of(i) = theta_lo + i * (theta_hi - theta_lo) / (rows - 1);
function phi_of(j)   = j * 360 / cols;

// Nominal grid point on spheroid (no perturbation)
function pt_raw(i, j) = let(
    th = theta_of(i),
    ph = phi_of(j),
    s  = sin(th)
) [ outer_r * s * cos(ph),
    outer_r * s * sin(ph),
    outer_r * cos(th) * z_scale ];

// Perturbed grid point  (perturbation scaled by sin(theta) so poles stay clean)
function pt(i, j) = let(
    idx = (i * cols + j) % total_pts,
    base = pt_raw(i, j),
    sf   = sin(theta_of(i))        // scale offsets → 0 at poles
) [ base[0] + rx[idx] * sf,
    base[1] + ry[idx] * sf,
    base[2] + rz[idx] ];

// Fixed apex and nadir helpers
function apex()  = [0, 0,  outer_r * z_scale];
function nadir() = [0, 0, -outer_r * z_scale];

// ─────────────────────────────────────────────────────────────
//  ROD MODULE  — hull() capsule between two points
// ─────────────────────────────────────────────────────────────
module rod(p1, p2) {
    hull() {
        translate(p1) sphere(r = node_r);
        translate(p2) sphere(r = node_r);
    }
}

// ─────────────────────────────────────────────────────────────
//  MAIN ASSEMBLY
// ─────────────────────────────────────────────────────────────
difference() {
    union() {

        // ── ① GRID RODS ──────────────────────────────────────
        //   Five connection types per cell to create chaotic weave.
        //   Modular wrapping on j ensures no open seam.
        for (i = [0 : rows - 2]) {
            for (j = [0 : cols - 1]) {

                p00 = pt(i,   j);
                p10 = pt(i+1, j);
                p01 = pt(i,   (j + 1) % cols);
                p11 = pt(i+1, (j + 1) % cols);

                // Meridional  (straight down)
                rod(p00, p10);

                // Latitudinal  (around ring)
                rod(p00, p01);

                // Diagonal NE
                rod(p00, p11);

                // Diagonal NW  (cross-brace)
                p1m1 = pt(i+1, (j - 1 + cols) % cols);
                rod(p00, p1m1);

                // Long skip-diagonal  (2 rows, 2 columns)
                // → produces the big crossing sticks visible in the reference
                if (i < rows - 2) {
                    p22 = pt(i+2, (j + 2) % cols);
                    rod(p00, p22);
                    p2m2 = pt(i+2, (j - 2 + cols) % cols);
                    rod(p00, p2m2);
                }
            }
        }

        // Close the final latitudinal ring at the bottom row
        for (j = [0 : cols - 1]) {
            rod(pt(rows-1, j), pt(rows-1, (j+1) % cols));
        }

        // ── ② APEX HUB ───────────────────────────────────────
        //   A solid sphere at the very top; every top-row node
        //   fans into it → no dangling ends up there.
        translate(apex()) sphere(r = top_hub_r, $fn = 30);
        for (j = [0 : cols - 1]) {
            rod(apex(), pt(0, j));
        }

        // ── ③ BASE RING ───────────────────────────────────────
        //   Solid torus-ring at the bottom for the lamp to rest on.
        //   Sits at the z-level of the bottom row of nodes.
        base_z = pt(rows-1, 0)[2];
        translate([0, 0, base_z - base_ring_h + rod_r])
            difference() {
                cylinder(r = base_ring_r + base_ring_w,
                         h = base_ring_h,
                         $fn = 60);
                translate([0, 0, -0.5])
                    cylinder(r = base_ring_r,
                             h = base_ring_h + 1,
                             $fn = 60);
            }

        // Connect every bottom-row node down to the base ring
        for (j = [0 : cols - 1]) {
            p_bot  = pt(rows-1, j);
            // Ring contact point directly below the node (same phi)
            phi_r  = atan2(p_bot[1], p_bot[0]);
            p_ring = [ (base_ring_r + base_ring_w/2) * cos(phi_r),
                       (base_ring_r + base_ring_w/2) * sin(phi_r),
                       base_z - base_ring_h/2 ];
            rod(p_bot, p_ring);
        }

    } // end union

    // ── ④ BOTTOM LIGHT OPENING ────────────────────────────────
    //   Cylinder punched from below → exposes bulb, lets light out.
    translate([0, 0, -(outer_r * z_scale + 2)])
        cylinder(r  = bottom_cut_r,
                 h  = outer_r * z_scale * 0.55 + 2,
                 $fn = 60);

} // end difference

// ═══════════════════════════════════════════════════════════════
//  TUNING CHEAT-SHEET
//
//  Denser / finer mesh     →  rows ↑,  cols ↑
//  Thicker rods            →  rod_r ↑
//  More chaos              →  perturb ↑  (try 10–15)
//  Different nest shape    →  seed  (any integer)
//  Taller shape            →  z_scale → 1.0
//  Bigger print            →  outer_r ↑  (e.g. 110)
//  Larger bulb opening     →  bottom_cut_r ↑
//  Faster preview          →  $fn = 4,  remove long-skip rods
// ═══════════════════════════════════════════════════════════════
