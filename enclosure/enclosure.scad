box_w = 130;
box_h = 110;
box_d = 45;
box_r = 4;

sw_r = 28/2;
// offset from edge
sw_o = box_r + 6 + sw_r;

sw_ox = sw_o;
sw_oy = sw_o+3;

mh = 20;

// raspberry pi sizes
pi_w = 85;
pi_h = 56;
pi_d = 1.6;
pi_x = -15;
pi_y = -15;
rpi_rise_i = 1.5;

module rpi(pcb=false) {

	rise = 8;
	rise_r = 5;
	rpi_rise_i = 1.5;

	translate([-pi_w/2 +5, -pi_h/2 +12.5, -0.1]) {
		difference() {
			cylinder(h=rise+0.1, r=rise_r, $fn=20);
			cylinder(h=rise+0.2, r=rpi_rise_i, $fn=20);
		}
	}
	translate([pi_w/2 - 25.5, pi_h/2 - 18, -0.1]) {
		difference() {
			cylinder(h=rise+0.1, r=rise_r, $fn=20);
			cylinder(h=rise+0.2, r=rpi_rise_i, $fn=20);
		}
	}

	if(pcb) {
		translate([0,0,rise+pi_d/2]) {
			color([0, 1, 0]) cube(size=[pi_w,pi_h,pi_d], center=true);
			translate([pi_w/2 - 31, pcb_h, 0]) {
				translate([-10, 30, 0]) {
					color([0, 0, 0]) cube(size=[20, 60, 10], center=true);
				}
			}
		}
	}
}

module roundedBox(size, radius, sidesonly)
{
	rot = [ [0,0,0], [90,0,90], [90,90,0] ];
	if (sidesonly) {
		cube(size - [2*radius,0,0], true);
		cube(size - [0,2*radius,0], true);
		for (x = [radius-size[0]/2, -radius+size[0]/2],
				 y = [radius-size[1]/2, -radius+size[1]/2]) {
			translate([x,y,0]) cylinder(r=radius, h=size[2], center=true);
		}
	}
	else {
		cube([size[0], size[1]-radius*2, size[2]-radius*2], center=true);
		cube([size[0]-radius*2, size[1], size[2]-radius*2], center=true);
		cube([size[0]-radius*2, size[1]-radius*2, size[2]], center=true);

		for (axis = [0:2]) {
			for (x = [radius-size[axis]/2, -radius+size[axis]/2],
					y = [radius-size[(axis+1)%3]/2, -radius+size[(axis+1)%3]/2]) {
				rotate(rot[axis]) 
					translate([x,y,0]) 
					cylinder(h=size[(axis+2)%3]-2*radius, r=radius, center=true);
			}
		}
		for (x = [radius-size[0]/2, -radius+size[0]/2],
				y = [radius-size[1]/2, -radius+size[1]/2],
				z = [radius-size[2]/2, -radius+size[2]/2]) {
			translate([x,y,z]) sphere(radius);
		}
	}
}

module outer() {
	screw_radius = 1.65;
	module screw_pillar_hole(x, y) {
		translate([x*(box_w/2 - box_r - 1.7), y*(box_h/2 - box_r - 1.7), 0]) {
			cylinder(h = box_d + 1, r = 1.7, $fn = 10, center = true);

			translate([0, 0, -(box_d/2 - 1.5)]) {
				//cylinder(h = 3, r = 3.25, $fn = 12, center = true);
			}
		}
	}
	module screw_pillar(x, y) {
		translate([x*(box_w/2 - box_r - 1.7), y*(box_h/2 - box_r - 1.7), 0]) {
			cylinder(h = box_d-box_r*2, r = 4.5, $fn = 20, center = true);
		}
	}

	translate([0, 0, box_d/2]) {
		difference() {
			union() {
				difference() {
					roundedBox(size=[box_w,box_h,box_d], radius=box_r, sidesonly=false);
					difference() {
						roundedBox(size=[box_w-(box_r*2),box_h-(box_r*2),box_d-(box_r*2)], radius=box_r, sidesonly=true);
						
						screw_pillar(+1, +1);
						screw_pillar(+1, -1);
						screw_pillar(-1, +1);
						screw_pillar(-1, -1);
					}
					
					screw_pillar_hole(+1, +1);
					screw_pillar_hole(+1, -1);
					screw_pillar_hole(-1, +1);
					screw_pillar_hole(-1, -1);

				}

				for(x=[-1,1]) for(y=[-1,1]) {
					translate([x*mh, y*mh, -(box_d/2 - box_r)]) {
						difference() {
							cylinder(h=3, r=5, $fn=30);
							cylinder(h=3+0.1, r=3.2, $fn=6);
						}					
					}
				}
			}

			for(i=[-1,1]) {
				translate([i*((box_w/2)-sw_ox), ((box_h/2)-sw_oy), 0 ]) {
					cylinder(h=box_d, r=sw_r, $fn=50);
				}
			}

			for(x=[-1,1]) for(y=[-1,1]) {
				translate([x*mh, y*mh, -(box_d/2 - box_r/2)])
					cylinder(h=box_r+0.1, r=1.65, center=true, $fn=20);
			}
			// bottom port
			translate([-10, box_h/2 - box_r/2, -5])
				cube(size=[60, box_r+0.5, 22], center=true);

			// side port
			translate([-(box_w/2 -box_r/2), -8, 0])
				cube(size=[box_r+0.5, 40, 22], center=true);

			// elongate rpi mount holes
			
			translate([pi_x, pi_y, -box_d/2]) {
				translate([-pi_w/2 +5, -pi_h/2 +12.5, 0]) {
					cylinder(h=box_r, r=rpi_rise_i, $fn=20);
				}
				translate([pi_w/2 - 25.5, pi_h/2 - 18, 0]) {
					cylinder(h=box_r, r=rpi_rise_i, $fn=20);
				}
			}

		}
	}
}

module case() {
	translate([0,0,-box_r])
		outer();

	translate([pi_x, pi_y, 0])
		rpi(pcb=false);
}

module base() {
	difference() {
		case();
		translate([0, 0, box_d-1.5*box_r]) {
			cube(size=[box_w+5, box_h+5, box_r+0.1], center=true);
		}
	}
}

module top() {
	difference() {
		case();
		cube(size=[box_w+5, box_h+5, (box_d-box_r*2)*2], center=true);
	}
}

module bracket() {
	// radius of central hole of bracket
	br_r = 10.2;
	// thickness of bracket
	br_th = 6;
	br_h = 8;
	// radius of dimple on pole
	br_d_r = 1.5;

	module bracket_ring() {
		union() {
			difference() {
				cylinder(h=br_h, r=br_r + br_th, center=true, $fn = 50);
				cylinder(h=br_h+0.1, r = br_r, center=true, $fn = 50);
			}
			translate([0, br_r-0.5, 0]) cylinder(h=br_h, r = br_d_r, center=true, $fn=20);
		}
	}

	difference() {
		bracket_ring();
		translate([0, -br_r-br_th-3, 0]) cylinder(h=br_h+0.1, r = br_r+br_th, center=true, $fn=50);
	}
	for(i=[-1,1]) rotate([0,i*90+90, 0]) {
		translate([13, -2, 0]) {
			translate([0, -8, 0]) {
				cube(size=[6, 16, br_h], center=true);
			}
			translate([7, -16 + br_th/2, 0]) {
				difference() {
					cube(size=[8, br_th, br_h], center=true);
					rotate([90,0,0])cylinder(h=br_h+0.1, r = 1.8, center=true, $fn=30);
				}
			}
		}
	}
}

// enclosure
if(0) {
	if(1) {
		if(1) {
			base();
		} else {
			top();
		}
		
	} else {
		case();
	}
} else {
	// bracket
	bracket();
}


//

if(0) {
	for(i=[-1,1]) {
		translate([i*((box_w/2)-sw_ox), ((box_h/2)-sw_oy), (box_d-box_r - 30/2) ]) {
			color([1, 0, 1]) cylinder(h=30, r=27/2, center=true);
		}
	}
}