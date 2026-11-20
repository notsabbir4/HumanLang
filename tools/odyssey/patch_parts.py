# ---------------------------------------------------------------- header notes and state
sub("note: HUMANLANG ODYSSEY: SEVEN WORLDS (the first slice). Made with HumanLang 0.6.2.",
    "note: HUMANLANG ODYSSEY: SEVEN WORLDS. Made with HumanLang 0.6.2.")
sub("note: Your logo reveal plays first (play video), then the title, the Motherboard hub, World 1 (Say Hello) and\nnote: World 5 (Platform Peaks).",
    "note: Your logo reveal plays first (play video), then the title and the Motherboard hub with its seven worlds:\nnote: 1 Say Hello, 2 Lists and Machines, 3 Word and Number Town, 4 Pixel Gallery, 5 Platform Peaks, 6 The Boss Citadel, 7 Your World.")
sub("note: Keys: left/right run, space jumps, enter talks, opens doors and confirms. On a phone: arrows, A = jump, B = enter.",
    "note: Keys: left/right run, space jumps, enter talks, opens doors and confirms. World 4 and 7 explain their keys on the screen.")
sub("set w1_done to 0\nset w5_done to 0\nset w5_best to 0\n",
    "set wdone to list of 0, 0, 0, 0, 0, 0, 0\nset w5_best to 0\nset w6_best to 0\nset wn to 1\nset echo_x to 0\nset g1_x to 0\nset g2_x to 0\nset portal_x to 0\nset done_world to 1\nset k_x to no\nset k_e to no\nset k_s to no\nset k_l to no\n")
sub('set sky_w5 to', 'set sky_w2 to list of "#05060F", "#080A1A", "#0B0F26", "#0F1533", "#131C42", "#182450", "#1D2C5E", "#22346C", "#273C7A"\nset sky_boss to list of "#12030A", "#1D0510", "#2A0716", "#3A091C", "#4A0C22", "#5C0F28", "#70132E", "#841834", "#98203C"\nset sky_w5 to')
sub('"WORLD_NAMES"', '"WORLD_NAMES"') if False else None
sub('set world_tips to list of "Talk to Echo and open the code gates.", "Build machines that sort and count.", "Puzzles with words and numbers.", "Paint your own pixel art.", "Run, jump and stomp the glitch bugs!", "A long boss fight. Dodge everything.", "Build, save and play your own level."',
    'set world_tips to list of "Talk to Echo and open the code gates.", "Lists, pits and bugs. Read the code.", "Puzzles with words and numbers.", "Paint the picture, one pixel at a time.", "Run, jump and stomp the glitch bugs!", "Stomp the Glitch King. Dodge his bolts.", "Build, save and play your own level."')

# ---------------------------------------------------------------- saving
replace_def("load_save", '''define load_save
    for each i from 1 to 7
        set v to recall "odyssey done {i}"
        if v is not nothing
            change item i of wdone to v
    set v to recall "odyssey coins"
    if v is not nothing
        change coins_total to v
    set v to recall "odyssey w5 best"
    if v is not nothing
        change w5_best to v
    set v to recall "odyssey w6 best"
    if v is not nothing
        change w6_best to v''')
replace_def("save_all", '''define save_all
    for each i from 1 to 7
        remember (item i of wdone) as "odyssey done {i}"
    remember coins_total as "odyssey coins"
    remember w5_best as "odyssey w5 best"
    remember w6_best as "odyssey w6 best"''')

# ---------------------------------------------------------------- starting places
replace_def("start_w1", '''define start_gw with n
    change mode to "gw"
    change wn to n
    load_gw_data with n
    change hp to 3
    change coins to 0
    change world_t to 0
    change gate1_open to no
    change gate2_open to no
    change scroll_got to list of 0, 0, 0
    change scroll_n to 0
    change echo_seen to no
    change gate2_seen to no
    change pz to 0
    change talk_on to no
    change done_t to 0
    place_hero with 40 and 184
    if n is 2
        play the music "chase"
    otherwise
        play the music "adventure"''')
sub('    change coin_got to {{W5_COIN_GOT}}\n', '    change coin_got to {{W5_COIN_GOT}}\n    change done_t to 0\n')
sub('    place_hero with 40 and 168\n    play the music "chase"', '    place_hero with 40 and 168\n    play the music "chase"')

# ---------------------------------------------------------------- the hero walks on the right map
sub('''    if mode is "hub"
        update the body hero on the map hubmap with solid "C"
    otherwise if mode is "w1"
        update the body hero on the map w1map with solid "G" and "D" and "E"
    otherwise
        update the body hero on the map w5map with solid "N" and "S"''', '''    if mode is "hub"
        update the body hero on the map hubmap with solid "C"
    otherwise if mode is "gw"
        if wn is 1
            update the body hero on the map w1map with solid "G" and "D" and "E"
        otherwise if wn is 2
            update the body hero on the map w2map with solid "M" and "m"
        otherwise
            update the body hero on the map w3map with solid "G" and "D" and "E"
    otherwise if mode is "w5"
        update the body hero on the map w5map with solid "N" and "S"
    otherwise if mode is "w6"
        update the body hero on the map w6map with solid "C" and "S"
    otherwise
        update the body hero on the map usermap with solid "G" and "D" and "S"''')

sub("give back (not talk_on) and pz is 0 and done_t is 0", "give back (not talk_on) and pz is 0 and done_t is 0 and not (mode is \"w7\" and edit_on)")

# ---------------------------------------------------------------- scrolls say their own text
sub("say_msg with (item i of scroll_text)", "say_msg with (item ((wn - 1) * 3 + i) of scroll_text)")

# ---------------------------------------------------------------- decor
replace_def("draw_decor", '''define draw_decor
    for each i from 1 to length of decor_k
        set dx to item i of decor_x
        if dx is greater than cam_x - 80 and dx is less than cam_x + 500
            set k to item i of decor_k
            set dy to item i of decor_y
            if k is 1
                draw the sprite tree at dx - 22, dy - 76
            otherwise if k is 2
                draw the sprite bush at dx, dy - 20
            otherwise if k is 3
                draw the sprite flower_a at dx, dy - 16
            otherwise if k is 4
                draw the sprite flower_b at dx, dy - 16
            otherwise if k is 5
                draw the sprite tuft at dx, dy - 10
            otherwise if k is 6
                draw the sprite rock at dx, dy - 16
            otherwise if k is 7
                draw the sprite pine at dx - 10, dy - 72
            otherwise if k is 8
                draw the sprite sign at dx, dy - 34
            otherwise if k is 9
                draw the sprite gear at dx, dy - 30 frame 1 + (floor of (tick / 20)) mod 2
            otherwise if k is 10
                draw the sprite crate at dx, dy - 24
            otherwise if k is 11
                draw the sprite lamp at dx, dy - 58
            otherwise if k is 12
                draw the sprite house_a at dx - 20, dy - 70
            otherwise if k is 13
                draw the sprite house_b at dx - 20, dy - 70''')

# ---------------------------------------------------------------- the worlds' pictures
replace_def("draw_w1_world", '''define draw_w1_world
    move the camera to 0, 0
    put a rectangle at 0, 0 with width 480 and height 270 and colour "#2F7FE8"
    backdrop with 1 and 0.17
    move the camera to cam_x, 0
    if wn is 1
        draw the map w1map
    otherwise
        draw the map w3map
    draw_decor

define draw_w2_world
    move the camera to 0, 0
    bands with sky_w2
    for each i from 1 to 36
        set sx to (i * 97) mod 480
        set sy to (i * 53) mod 130
        if (floor of ((tick + i * 13) / 25)) mod 4 is not 0
            put a rectangle at sx, sy with width 2 and height 2 and colour "#FFB85E"
    for each k from 0 to 4
        draw the sprite tower at k * 130 - (scrolled with 0.3) + 10, 70 frame 1 + (floor of ((tick + k * 20) / 40)) mod 2
    move the camera to cam_x, 0
    draw the map w2map
    draw_decor''')

# ---------------------------------------------------------------- hub
sub("define scrolled with f\n    give back (cam_x * f) mod 224", "define scrolled with f\n    give back (cam_x * f) mod 224\n\ndefine tower_off with f\n    give back (cam_x * f) mod 130")
sub("k * 130 - (scrolled with 0.3) + 10", "k * 130 - (tower_off with 0.3) + 10")
sub("k * 130 - (scrolled with 0.35) + 10", "k * 130 - (tower_off with 0.35) + 10")
replace_def("draw_hub_door", '''define draw_hub_door with i and dx
    draw the sprite door at dx, 168 frame i
    shadow_text with "{i}" and (dx + 17) and 138 and 18 and "#FFFFFF" and "center"
    if item i of wdone is 1
        draw the sprite star at dx + 12, 122''')
sub('''    if k_enter and near_door is greater than 0
        if near_door is 1
            start_w1
        otherwise if near_door is 5
            start_w5
        otherwise
            play the sound "lose"
            say_msg with "This world is coming in the full game."''', '''    if k_enter and near_door is greater than 0
        play the sound "powerup"
        if near_door is less than 4
            start_gw with near_door
        otherwise if near_door is 4
            start_w4
        otherwise if near_door is 5
            start_w5
        otherwise if near_door is 6
            start_w6
        otherwise
            start_w7''')
sub('''        if i is 1 or i is 5
            text_at with "Enter: go in" and 240 and 238 and 10 and "#8FF2AE" and "center"
        otherwise
            text_at with "Locked: coming in the full game" and 240 and 238 and 10 and "#FF8E8E" and "center"''', '''        text_at with "Enter: go in" and 240 and 238 and 10 and "#8FF2AE" and "center"''')
sub("    set done_count to w1_done + w5_done\n", "    set done_count to sum of wdone\n")
sub('''    if w1_done is 1 or w5_done is 1
        shadow_text with "Your progress was loaded."''', '''    if (sum of wdone) is greater than 0
        shadow_text with "Your progress was loaded."''')

# ---------------------------------------------------------------- the code panel knows which gate of the world it is
sub('text_at with "CODE GATE {pz}" and 240 and 38 and 15 and "#FFE680" and "center"', 'set gate_n to ((pz - 1) mod 2) + 1\n        text_at with "CODE GATE {gate_n}" and 240 and 38 and 15 and "#FFE680" and "center"')
sub('''                    if pz is 1
                        change gate1_open to yes''', '''                    if ((pz - 1) mod 2) is 0
                        change gate1_open to yes''')

# ---------------------------------------------------------------- gate worlds (1, 2 and 3)
replace_def("w1_gate_block", '''define gw_gate_block
    note: a closed gate is a wall: the hero cannot go through it
    set hx to the x of the body hero
    if not gate1_open and hx is greater than g1_x - 26
        move the body hero to g1_x - 26, (the y of the body hero)
    if not gate2_open and hx is greater than g2_x - 26
        move the body hero to g2_x - 26, (the y of the body hero)''')
replace_def("update_w1", '''define update_gw
    update_talk
    update_panel
    add 1 to world_t
    hero_move
    gw_gate_block
    follow_camera
    if hurt_t is greater than 0
        subtract 1 from hurt_t
    set hx to the x of the body hero
    note: Echo says hello the first time you walk up to him
    if not echo_seen and not talk_on and hx is greater than echo_x - 90
        start_talk with (item wn of echo_a_all) and (item wn of echo_b_all) and "echo"
    if not gate2_seen and not talk_on and gate1_open and hx is greater than g2_x - 150
        start_talk with (item wn of echo2_a_all) and (item wn of echo2_b_all) and "gate2"
    if hero_free
        pick_up_coins
        pick_up_scrolls
        update_bugs
        update_flags
        hazards
        if k_enter
            if not gate1_open and hx is greater than g1_x - 90 and hx is less than g1_x
                change pz to (wn - 1) * 2 + 1
                change pz_sel to 1
                change pz_stage to "pick"
            otherwise if gate1_open and not gate2_open and hx is greater than g2_x - 90 and hx is less than g2_x
                change pz to (wn - 1) * 2 + 2
                change pz_sel to 1
                change pz_stage to "pick"
            otherwise if hx is greater than echo_x - 50 and hx is less than echo_x + 60
                start_talk with (item wn of echo_a_all) and (item wn of echo_b_all) and "echo"
        if gate2_open and hx is greater than portal_x - 20 and hx is less than portal_x + 34
            finish_world with wn
    if wn is 2
        draw_w2_world
    otherwise
        draw_w1_world
    draw_scrolls
    draw_coins
    draw_flags
    draw the sprite echo at echo_x, 170 frame 1 + (floor of (tick / 40)) mod 2 facing left
    set g1f to 1
    if gate1_open
        set g1f to 2
    set g2f to 1
    if gate2_open
        set g2f to 2
    draw the sprite gate at g1_x, 154 frame g1f
    draw the sprite gate at g2_x, 154 frame g2f
    draw the sprite portal at portal_x, 160 frame 1 + (floor of (tick / 8)) mod 3
    draw_bugs
    draw_hero
    move the camera to 0, 0
    if not gate1_open and hx is greater than g1_x - 90 and hx is less than g1_x and pz is 0 and not talk_on
        shadow_text with "Enter: read the gate" and 240 and 170 and 12 and "#FFE680" and "center"
    if gate1_open and not gate2_open and hx is greater than g2_x - 90 and hx is less than g2_x and pz is 0 and not talk_on
        shadow_text with "Enter: read the gate" and 240 and 170 and 12 and "#FFE680" and "center"
    set title to "WORLD {wn}: {item wn of world_names}"
    draw_hud with title
    text_at with "Scrolls {scroll_n}/3" and 470 and 26 and 11 and "#FFE680" and "right"
    draw_talk
    draw_panel
    change k_enter to no''')
drop_def("finish_w1")
drop_def("draw_w1_done")

# ---------------------------------------------------------------- hazards look at the right map
replace_def("hazards", '''define tile_under with x and y
    if mode is "gw"
        if wn is 1
            give back tile at x, y of w1map
        otherwise if wn is 2
            give back tile at x, y of w2map
        otherwise
            give back tile at x, y of w3map
    otherwise if mode is "w5"
        give back tile at x, y of w5map
    otherwise if mode is "w7"
        give back tile at x, y of usermap
    give back ""

define hazards
    set hx to the x of the body hero
    set hy to the y of the body hero
    set under to tile_under with (hx + 11) and (hy + 41)
    if under is "^" or hy is greater than 262
        if hy is greater than 262
            respawn_hero
        otherwise
            hurt_hero
            if hurt_t is 100
                move the body hero to hx, hy - 30
                make the body hero bounce''')

# ---------------------------------------------------------------- finishing worlds
replace_def("finish_w5", '''define finish_world with n
    change done_world to n
    change mode to "wdone"
    change done_t to 1
    change item n of wdone to 1
    change coins_total to coins_total + coins
    save_all
    play the sound "win"

define finish_w5
    set secs to floor of (world_t / 60)
    change last_time to secs
    if w5_best is 0 or secs is less than w5_best
        change w5_best to secs
    finish_world with 5''')
replace_def("draw_w5_done", '''define draw_wdone
    set n to done_world
    set total_coins to length of coin_x
    set l1 to "Coins {coins}"
    if n is less than 4
        set l1 to "Coins {coins}/{total_coins}     Scrolls {scroll_n}/3"
    if n is 4
        set l1 to "Every pixel is right!"
    if n is 5
        set clock to clock_text with last_time
        set l1 to "Coins {coins}/{total_coins}     Time {clock}"
    if n is 6
        set clock to clock_text with last_time
        set l1 to "The Glitch King is beaten in {clock}"
    if n is 7
        set l1 to "You made a level and you beat it!"
    draw_done with "WORLD {n} COMPLETE" and l1 and (item n of done_lines)
    if k_enter
        if (sum of wdone) is 7 and not ending_seen
            change mode to "ending"
            change ending_seen to yes
        otherwise
            start_hub with ((item n of door_x) + 6)''')
sub("set w5_final to 0\n\n", "")

# ---------------------------------------------------------------- more state, data lists and the new worlds
sub("set near_door to 0\n", '''set near_door to 0
set last_time to 0
set ending_seen to no
set k_up to no
set k_down to no
set edit_on to yes
set canvas to empty list
set cx to 0
set cy to 0
set pcol to 1
set boss_hp to 12
set boss_max to 12
set boss_x to 300
set boss_dir to -1
set boss_stun to 0
set bolt_t to 0
set bolt_x to empty list
set bolt_y to empty list
set bolt_w to empty list
set bolt_on to empty list
set ux to 0
set uy to 0
set utile to 1
set level_backup to ""
set user_loaded to no
''')

new_worlds = r'''
note: ==================================================
note: WORLD 4: PIXEL GALLERY (paint the picture)
note: ==================================================

define start_w4
    change mode to "w4"
    change world_w to 480
    change coins to 0
    change world_t to 0
    change done_t to 0
    change hp to 3
    change cam_x to 0
    change canvas to empty list
    for each i from 1 to 144
        add 0 to canvas
    change cx to 0
    change cy to 0
    change pcol to 1
    change coin_x to empty list
    change coin_y to empty list
    change coin_got to empty list
    play the music "chill"

define count_match
    set same to 0
    for each i from 1 to 144
        if (item i of canvas) is (item i of paint_target)
            add 1 to same
    give back same

define cell_colour with v
    if v is 0
        give back "#141C3E"
    give back item v of paint_pal

define update_w4
    add 1 to world_t
    if k_left and cx is greater than 0
        subtract 1 from cx
    if k_right and cx is less than 11
        add 1 to cx
    if k_up and cy is greater than 0
        subtract 1 from cy
    if k_down and cy is less than 11
        add 1 to cy
    if key "1" is down
        change pcol to 1
    if key "2" is down
        change pcol to 2
    if key "3" is down
        change pcol to 3
    if key "4" is down
        change pcol to 4
    set at to cy * 12 + cx + 1
    if key "space" is down
        change item at of canvas to pcol
    if key "x" is down
        change item at of canvas to 0
    set same to count_match
    if same is 144 and done_t is 0
        finish_world with 4
    move the camera to 0, 0
    bands with sky_hub
    draw the sprite easel at 30, 214
    draw the sprite easel at 420, 214
    put a rectangle at 14, 34 with width 170 and height 170 and colour "#0B1026" and border 2 and border colour "#FFE680" and rounded 6
    for each i from 1 to 144
        set r to floor of ((i - 1) / 12)
        set c to (i - 1) mod 12
        set colr to cell_colour with (item i of canvas)
        put a rectangle at 20 + c * 13, 40 + r * 13 with width 12 and height 12 and colour colr
    set cur to cell_colour with (item at of canvas)
    put a rectangle at 20 + cx * 13 - 1, 40 + cy * 13 - 1 with width 14 and height 14 and colour cur and border 2 and border colour "#FFFFFF"
    text_at with "YOUR PICTURE" and 99 and 210 and 10 and "#9AA3C0" and "center"
    put a rectangle at 232, 34 with width 110 and height 110 and colour "#0B1026" and border 2 and border colour "#7FD6FF" and rounded 6
    for each i from 1 to 144
        set r to floor of ((i - 1) / 12)
        set c to (i - 1) mod 12
        set colr to cell_colour with (item i of paint_target)
        put a rectangle at 238 + c * 8, 40 + r * 8 with width 8 and height 8 and colour colr
    text_at with "COPY THIS" and 287 and 148 and 10 and "#9AA3C0" and "center"
    for each o from 1 to 4
        set pc to item o of paint_pal
        set bc to "#3B4A7A"
        if o is pcol
            set bc to "#FFFFFF"
        put a rectangle at 360 + (o - 1) * 28, 40 with width 24 and height 24 and colour pc and border 2 and border colour bc and rounded 4
        text_at with "{o}" and (372 + (o - 1) * 28) and 68 and 11 and "#FFFFFF" and "center"
    text_at with "Arrows move" and 360 and 96 and 11 and "#FFFFFF" and "left"
    text_at with "Space paints" and 360 and 112 and 11 and "#FFFFFF" and "left"
    text_at with "1 2 3 4 pick a colour" and 360 and 128 and 11 and "#FFFFFF" and "left"
    text_at with "X rubs out" and 360 and 144 and 11 and "#FFFFFF" and "left"
    text_at with "Matching squares: {same}/144" and 360 and 168 and 11 and "#8FF2AE" and "left"
    text_at with "In HumanLang a picture is" and 232 and 196 and 10 and "#9AA3C0" and "left"
    text_at with "just letters: put pixel art" and 232 and 210 and 10 and "#9AA3C0" and "left"
    draw_hud with "WORLD 4: PIXEL GALLERY"
    change k_enter to no

note: ==================================================
note: WORLD 6: THE BOSS CITADEL (the Glitch King)
note: ==================================================

define start_w6
    change mode to "w6"
    change world_w to 480
    change hp to 3
    change coins to 0
    change world_t to 0
    change done_t to 0
    change boss_hp to boss_max
    change boss_x to 300
    change boss_dir to -1
    change boss_stun to 0
    change bolt_t to 0
    change bolt_x to empty list
    change bolt_y to empty list
    change bolt_w to empty list
    change bolt_on to empty list
    change coin_x to empty list
    change coin_y to empty list
    change coin_got to empty list
    change decor_k to empty list
    change decor_x to empty list
    change decor_y to empty list
    change bug_x to empty list
    change bug_y to empty list
    change bug_lo to empty list
    change bug_hi to empty list
    change bug_dir to empty list
    change bug_alive to empty list
    change flag_x to empty list
    change flag_y to empty list
    change flag_on to empty list
    place_hero with 40 and 184
    play the music "boss"

define boss_phase
    give back 1 + floor of ((boss_max - boss_hp) / 4)

define add_bolt with x
    set slot to 0
    for each i from 1 to length of bolt_x
        if slot is 0 and (item i of bolt_on) is 0
            set slot to i
    if slot is 0
        add x to bolt_x
        add -30 to bolt_y
        add 50 to bolt_w
        add 1 to bolt_on
    otherwise
        change item slot of bolt_x to x
        change item slot of bolt_y to -30
        change item slot of bolt_w to 50
        change item slot of bolt_on to 1

define update_boss
    set phase to boss_phase
    set boss_y to 152
    if boss_stun is greater than 0
        subtract 1 from boss_stun
    otherwise
        change boss_x to boss_x + boss_dir * (0.8 + 0.5 * phase)
        if boss_x is less than 20
            change boss_x to 20
            change boss_dir to 1
        if boss_x is greater than 396
            change boss_x to 396
            change boss_dir to -1
    set hx to the x of the body hero
    set hy to the y of the body hero
    set vy to the vertical speed of the body hero
    if hx + 22 is greater than boss_x + 6 and hx is less than boss_x + 58 and hy + 40 is greater than 146 and hy is less than 224
        if boss_stun is 0
            if vy is greater than 0.3 and hy + 40 is less than 182
                subtract 1 from boss_hp
                change boss_stun to 80
                make the body hero bounce
                play the sound "explosion"
                add 5 to coins
                say_msg with "Hit! {boss_hp} to go."
                if boss_hp is at most 0
                    finish_boss
            otherwise
                hurt_hero
                if hurt_t is 100
                    set side to 30
                    if hx is less than boss_x + 32
                        set side to -30
                    set nx to hx + side
                    if nx is less than 20
                        set nx to 20
                    if nx is greater than 438
                        set nx to 438
                    move the body hero to nx, hy - 8
    add 1 to bolt_t
    if bolt_t is greater than 200 - 35 * phase
        change bolt_t to 0
        add_bolt with (hx + 5)

define update_bolts
    set hx to the x of the body hero
    set hy to the y of the body hero
    for each i from 1 to length of bolt_x
        if (item i of bolt_on) is 1
            if (item i of bolt_w) is greater than 0
                change item i of bolt_w to (item i of bolt_w) - 1
            otherwise
                change item i of bolt_y to (item i of bolt_y) + 5
                set bx to item i of bolt_x
                set by to item i of bolt_y
                if hx + 22 is greater than bx and hx is less than bx + 12 and hy + 40 is greater than by and hy is less than by + 22
                    change item i of bolt_on to 0
                    hurt_hero
                if by is greater than 222
                    change item i of bolt_on to 0

define draw_boss
    set bf to 1 + (floor of (tick / 12)) mod 2
    if boss_stun is 0 or (floor of (tick / 3)) mod 2 is 0
        draw the sprite boss at boss_x, 152 frame bf

define draw_bolts
    for each i from 1 to length of bolt_x
        if (item i of bolt_on) is 1
            set bx to item i of bolt_x
            if (item i of bolt_w) is greater than 0
                if (floor of (tick / 4)) mod 2 is 0
                    draw the sprite warn at bx, 204
            otherwise
                draw the sprite bolt at bx, item i of bolt_y frame 1 + (floor of (tick / 4)) mod 2

define finish_boss
    set secs to floor of (world_t / 60)
    change last_time to secs
    if w6_best is 0 or secs is less than w6_best
        change w6_best to secs
    finish_world with 6

define draw_w6_world
    move the camera to 0, 0
    bands with sky_boss
    for each k from 0 to 4
        draw the sprite tower at k * 110 + 10, 100 frame 1 + (floor of ((tick + k * 20) / 40)) mod 2
    move the camera to 0, 0
    draw the map w6map

define update_w6
    add 1 to world_t
    hero_move
    follow_camera
    if hurt_t is greater than 0
        subtract 1 from hurt_t
    if done_t is 0
        update_boss
        update_bolts
        if (the y of the body hero) is greater than 262
            respawn_hero
    draw_w6_world
    draw_boss
    draw_bolts
    draw_hero
    move the camera to 0, 0
    put a rectangle at 150, 24 with width 180 and height 12 and colour "#2A0716" and border 2 and border colour "#FFFFFF" and rounded 4
    if boss_hp is greater than 0
        put a rectangle at 152, 26 with width boss_hp * 14 and height 8 and colour "#E43A4C" and rounded 3
    text_at with "THE GLITCH KING" and 240 and 38 and 10 and "#FFFFFF" and "center"
    draw_hud with "WORLD 6: THE BOSS CITADEL"
    change k_enter to no

note: ==================================================
note: WORLD 7: YOUR WORLD (build, save and play your own level)
note: ==================================================

define serialize_level
    set s to ""
    for each r from 1 to 14
        for each c from 1 to 30
            set t to tile in column c, row r of usermap
            if t is ""
                set t to "."
            set s to "{s}{t}"
    give back s

define apply_level with s
    for each r from 1 to 14
        for each c from 1 to 30
            set ch to item ((r - 1) * 30 + c) of s
            change tile in column c, row r of usermap to ch

define start_w7
    change mode to "w7"
    change world_w to 480
    change edit_on to yes
    change hp to 3
    change coins to 0
    change world_t to 0
    change done_t to 0
    change cam_x to 0
    change ux to 1
    change uy to 11
    change coin_x to empty list
    change coin_y to empty list
    change coin_got to empty list
    change decor_k to empty list
    change decor_x to empty list
    change decor_y to empty list
    change bug_x to empty list
    change bug_y to empty list
    change bug_lo to empty list
    change bug_hi to empty list
    change bug_dir to empty list
    change bug_alive to empty list
    change flag_x to empty list
    change flag_y to empty list
    change flag_on to empty list
    if not user_loaded
        change user_loaded to yes
        set v to recall "odyssey level"
        if v is not nothing
            if length of v is 420
                apply_level with v
    play the music "adventure"

define enter_play
    change level_backup to serialize_level
    change edit_on to no
    change coins to 0
    change hp to 3
    change hurt_t to 0
    place_hero with 20 and 60
    say_msg with "Reach the star! Press E to go back and edit."

define leave_play
    apply_level with level_backup
    change edit_on to yes
    change msg_t to 0

define update_w7
    add 1 to world_t
    if edit_on
        if k_left and ux is greater than 0
            subtract 1 from ux
        if k_right and ux is less than 29
            add 1 to ux
        if k_up and uy is greater than 0
            subtract 1 from uy
        if k_down and uy is less than 13
            add 1 to uy
        if key "1" is down
            change utile to 1
        if key "2" is down
            change utile to 2
        if key "3" is down
            change utile to 3
        if key "4" is down
            change utile to 4
        if key "5" is down
            change utile to 5
        if key "6" is down
            change utile to 6
        if key "space" is down
            change tile in column ux + 1, row uy + 1 of usermap to (item utile of user_letters)
        if key "x" is down
            change tile in column ux + 1, row uy + 1 of usermap to "."
        if k_s
            remember serialize_level as "odyssey level"
            say_msg with "Level saved!"
            play the sound "powerup"
        if k_l
            set v to recall "odyssey level"
            if v is not nothing
                apply_level with v
                say_msg with "Level loaded!"
        if k_enter
            enter_play
    otherwise
        hero_move
        follow_camera
        if hurt_t is greater than 0
            subtract 1 from hurt_t
        if done_t is 0
            set hx to (the x of the body hero) + 11
            set hy to (the y of the body hero) + 30
            set here to tile at hx, hy of usermap
            if here is "c"
                change tile at hx, hy of usermap to "."
                add 1 to coins
                play the sound "coin"
            hazards
            if here is "F"
                leave_play_for_finish
        if k_e
            leave_play
    move the camera to 0, 0
    put a rectangle at 0, 0 with width 480 and height 270 and colour "#2F7FE8"
    bands with sky_w1
    draw the map usermap
    if not edit_on
        draw_hero
    move the camera to 0, 0
    if edit_on
        set cur_x to ux * 16
        set cur_y to uy * 16
        put a rectangle at cur_x, cur_y with width 16 and height 2 and colour "#FFE680"
        put a rectangle at cur_x, cur_y + 14 with width 16 and height 2 and colour "#FFE680"
        put a rectangle at cur_x, cur_y with width 2 and height 16 and colour "#FFE680"
        put a rectangle at cur_x + 14, cur_y with width 2 and height 16 and colour "#FFE680"
    put a rectangle at 0, 226 with width 480 and height 44 and colour "#0B1026"
    if edit_on
        for each o from 1 to 6
            set bc to "#3B4A7A"
            if o is utile
                set bc to "#FFE680"
            put a rectangle at 8 + (o - 1) * 30, 232 with width 26 and height 26 and colour "#141C3E" and border 2 and border colour bc and rounded 4
            draw_tool with o and (14 + (o - 1) * 30) and 238
            text_at with "{o}" and (21 + (o - 1) * 30) and 259 and 9 and "#9AA3C0" and "center"
        text_at with "Arrows move   Space puts   X rubs out" and 196 and 234 and 10 and "#FFFFFF" and "left"
        text_at with "S saves   L loads   Enter plays your level" and 196 and 250 and 10 and "#8FF2AE" and "left"
    otherwise
        text_at with "Reach the star.   E: back to editing" and 240 and 240 and 12 and "#FFFFFF" and "center"
    draw_hud with "WORLD 7: YOUR WORLD"
    change k_enter to no

define draw_tool with o and x and y
    if o is 1
        draw the sprite t_grass at x - 4, y - 4
    otherwise if o is 2
        draw the sprite t_dirt at x - 4, y - 4
    otherwise if o is 3
        draw the sprite t_stone at x - 4, y - 4
    otherwise if o is 4
        draw the sprite t_spike at x - 4, y - 4
    otherwise if o is 5
        draw the sprite coin at x - 2, y - 2
    otherwise
        draw the sprite star at x - 1, y - 1

define leave_play_for_finish
    apply_level with level_backup
    finish_world with 7

note: ==================================================
note: THE END
note: ==================================================

define draw_ending
    move the camera to 0, 0
    put a rectangle at 0, 0 with width 480 and height 270 and colour "#0B1026"
    for each i from 1 to 30
        put a rectangle at (i * 83) mod 480, (i * 41 + tick) mod 270 with width 3 and height 3 and colour "#FFE680"
    shadow_text with "YOU DID IT!" and 240 and 20 and 30 and "#FFE680" and "center"
    draw the sprite hero at 208, 62 frame 11
    shadow_text with "All seven worlds are finished." and 240 and 128 and 15 and "#FFFFFF" and "center"
    shadow_text with "You can read and write HumanLang now." and 240 and 150 and 13 and "#8FF2AE" and "center"
    shadow_text with "Coins collected: {coins_total}" and 240 and 172 and 12 and "#FFE680" and "center"
    shadow_text with "Made with HumanLang by the HL mascot and you." and 240 and 196 and 11 and "#7FD6FF" and "center"
    if (floor of (tick / 25)) mod 2 is 0
        shadow_text with "Press ENTER to go back to the Motherboard" and 240 and 234 and 12 and "#FFFFFF" and "center"
    if k_enter
        start_hub with 60

'''
sub("note: ==================================================\nnote: THE GAME", new_worlds + "note: ==================================================\nnote: THE GAME")

# ---------------------------------------------------------------- the game itself
sub('''    when the key "space" is pressed
        change k_space to yes
''', '''    when the key "space" is pressed
        change k_space to yes

    when the key "up" is pressed
        change k_up to yes

    when the key "down" is pressed
        change k_down to yes

    when the key "e" is pressed
        change k_e to yes

    when the key "s" is pressed
        change k_s to yes

    when the key "l" is pressed
        change k_l to yes
''')
sub('''        otherwise if mode is "w1"
            update_w1
        otherwise if mode is "w1done"
            draw_w1_done
        otherwise if mode is "w5"
            update_w5
        otherwise if mode is "w5done"
            draw_w5_done''', '''        otherwise if mode is "gw"
            update_gw
        otherwise if mode is "w4"
            update_w4
        otherwise if mode is "w5"
            update_w5
        otherwise if mode is "w6"
            update_w6
        otherwise if mode is "w7"
            update_w7
        otherwise if mode is "wdone"
            draw_wdone
        otherwise if mode is "ending"
            draw_ending''')
sub("        change k_right to no\n        change k_space to no\n", "        change k_right to no\n        change k_space to no\n        change k_up to no\n        change k_down to no\n        change k_e to no\n        change k_s to no\n        change k_l to no\n")
sub("define start_gw with n", "{{GW_LOADER}}\n\ndefine start_gw with n")

# ---------------------------------------------------------------- the redesigned Motherboard
sub('update the body hero on the map hubmap with solid "C"', 'update the body hero on the map hubmap with solid "H" and "J" and "h" and "k"')
sub('''            otherwise if k is 13
                draw the sprite house_b at dx - 20, dy - 70''', '''            otherwise if k is 13
                draw the sprite house_b at dx - 20, dy - 70
            otherwise if k is 14
                draw the sprite terminal at dx, dy - 38
            otherwise if k is 15
                draw the sprite dish at dx, dy - 52 frame 1 + (floor of (tick / 30)) mod 2
            otherwise if k is 16
                draw the sprite fern at dx, dy - 24 frame 1 + (floor of ((tick + dx) / 40)) mod 2''')
replace_def("draw_hub_world", '''define draw_hub_world
    move the camera to 0, 0
    bands with sky_hub
    for each i from 1 to 44
        set sx to (i * 97) mod 480
        set sy to (i * 53) mod 150
        if (floor of ((tick + i * 13) / 25)) mod 4 is not 0
            put a rectangle at sx, sy with width 2 and height 2 and colour "#7FA8FF"
    set moon_x to 400 - floor of (cam_x * 0.03)
    put a circle at moon_x, 52 with radius 20 and colour "#9FB8F0"
    put a circle at moon_x - 1, 51 with radius 17 and colour "#D6E4FF"
    put a circle at moon_x + 6, 58 with radius 4 and colour "#B4C8F4"
    put a circle at moon_x - 7, 45 with radius 3 and colour "#B4C8F4"
    set lit to 1
    if (sum of wdone) is at least 3
        set lit to 2
    if (sum of wdone) is at least 6
        set lit to 3
    set far_off to floor of (cam_x * 0.1) mod 480
    draw the sprite city_far at 0 - far_off, 84
    draw the sprite city_far at 480 - far_off, 84
    set near_off to floor of (cam_x * 0.28) mod 480
    draw the sprite city_near at 0 - near_off, 112 frame lit
    draw the sprite city_near at 480 - near_off, 112 frame lit
    move the camera to cam_x, 0
    draw the sprite chip at {{CHIP_X}}, 74 frame 1 + (floor of (tick / 40)) mod 2
    draw the map hubmap
    draw_decor
    draw the sprite echo at 104, 170 frame 1 + (floor of (tick / 40)) mod 2 facing left
    for each i from 1 to 7
        set dx to item i of door_x
        draw_hub_door with i and dx
    move the camera to 0, 0
    for each i from 1 to 16
        set spx to (i * 131) mod 480
        set spy to 224 - ((tick * (0.3 + (i mod 3) * 0.2) + i * 41) mod 200)
        put a rectangle at spx, spy with width 2 and height 2 and colour "#7FE8FF"
    move the camera to cam_x, 0''')
replace_def("draw_hub_door", '''define draw_hub_door with i and dx
    set st to 1 + (floor of (tick / 30)) mod 2
    if item i of wdone is 1
        set st to 3
    draw the sprite portal_door at dx, 152 frame (i - 1) * 3 + st
    set label_x to floor of (dx + 25 - cam_x)
    shadow_text with "{i}" and label_x and 132 and 16 and "#FFFFFF" and "center"
    if item i of wdone is 1
        draw the sprite star at dx + 20, 116''')
sub("(item i of door_x) - 6 and hx is less than (item i of door_x) + 40", "(item i of door_x) - 6 and hx is less than (item i of door_x) + 56")
sub("define start_hub with x\n    change mode to \"hub\"\n", "define start_hub with x\n    change mode to \"hub\"\n    change decor_k to {{HUB_DECOR_K}}\n    change decor_x to {{HUB_DECOR_X}}\n    change decor_y to {{HUB_DECOR_Y}}\n")

sub('put a rectangle at 90, 196 with width 300 and height 56 and colour "#0B1026"', 'put a rectangle at 90, 36 with width 300 and height 58 and colour "#0B1026"')
sub('text_at with "WORLD {i}: {item i of world_names}" and 240 and 202 and 14', 'text_at with "WORLD {i}: {item i of world_names}" and 240 and 42 and 14')
sub('text_at with (item i of world_tips) and 240 and 224 and 11', 'text_at with (item i of world_tips) and 240 and 62 and 11')
sub('text_at with "Enter: go in" and 240 and 238 and 10 and "#8FF2AE" and "center"', 'text_at with "Enter: go in" and 240 and 77 and 10 and "#8FF2AE" and "center"')
