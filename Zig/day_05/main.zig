//
// main
// Zig version: 
// Author: Myles
// Date: 2020-12-05
//
const std = @import("std");

pub fn main() void{
    std.debug.print("[=] Advent of code day 5 \n", .{});
    var e: i32 = eval("FBFBBFFRLR");
}

// Quasi BSP algorithm
pub fn eval(input: []const u8 ) i32{
    var upr: i32 = 127;
    var low: i32 = 0;
    var mid: i32 = 127/2;


    std.debug.print("[=] input = {} \n", .{input});
    std.debug.print("[=] u = {}, l = {}, m = {} \n", .{upr, low, mid});
    // Iterate chars of input
    for (input) |ch|{
        std.debug.print("[-] char = {} \n", .{ch});

        // F = 70, B = 66, L = 76, R = 82
        if( ch == 70 ){
            upr = mid;
            mid = @divFloor((upr+low),2);
            std.debug.print("[=] u = {}, l = {}, m = {} \n", .{upr, low, mid});
        }
        if( ch == 66 ){
            low = mid;
            mid = @divFloor((upr+low),2);
            std.debug.print("[=] u = {}, l = {}, m = {} \n", .{upr, low, mid});
        }
        if( ch == 76 ){}
        if( ch == 82 ){}
    }

    return 0;
}