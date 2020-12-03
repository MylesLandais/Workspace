//
// main
// Zig version: 
// Author: Myles
// Date: 2020-12-02
//
const std = @import("std");
const fs = std.fs;

pub fn main() !void {
    var alloc = std.heap.GeneralPurposeAllocator(.{}){};
    const input = try std.fs.cwd().readFileAlloc(&alloc.allocator, "input.txt", std.math.maxInt(usize));

    var lines = std.mem.tokenize(input, "\n");

    var valid_count: i32 = 0;

    while (lines.next()) |line| {

        var parts = std.mem.tokenize(line, ": ");
        //std.debug.print("{} \n",.{line});
        const split = parts.next().?;
        const match_char = parts.next().?[0];
        const password = parts.next().?;
        var minmax = std.mem.tokenize(split, "-");
        const min = try std.fmt.parseInt(i32, minmax.next().?, 10);
        const max = try std.fmt.parseInt(i32, minmax.next().?, 10);


        if ( valid_pwd(min,max,match_char,password) == true) {
            valid_count += 1;
        }
    }

    std.debug.print("valid count of passwords: {}\n", .{ valid_count });
}

fn valid_pwd(min:i32, max:i32, match_char: u8, input:[]const u8) bool{
    var count: i32 = 0;
   for (input) |ch| {
       //std.debug.print("[-] match {} = {} ~ \n",.{ch,match_char});

       if(ch == match_char){
           count += 1;
           //std.debug.print("[+] count = {} ~ \n",.{count});
       }
   }
    if( count >= min and count <= max){
        //std.debug.print("password is good~ \n",.{});
        return true;
    }
   return false;
}