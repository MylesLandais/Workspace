const std = @import("std");
const input = @embedFile("input_2.txt");

var has_ecl: bool = false;
var has_pid: bool = false;
var has_eyr: bool = false;
var has_hcl: bool = false;
var has_byr: bool = false;
var has_iyr: bool = false;
var has_hgt: bool = false;

pub fn main() void{
    var count: i32 = 0;
    // iterator for chunks, splitting on two newlines (blank lines end of data set)
    var chunks = std.mem.split(input, "\r\n\r\n");

    while (chunks.next()) |chunk|{
        //std.debug.print("==/CHUNK==\n{}\n==CHUNK==\n", .{chunk});
        //process lines in chunk
        var lines = std.mem.split(chunk,"\r\n");
        //process key_pairs in data chunk
         while (lines.next()) |data|{
            var key_pair = std.mem.tokenize(data, " ");
            while(key_pair.next()) |kp|{
                //check length of kp
                //match first three chars
                if( std.mem.eql(u8, kp[0..3], "pid")){
          //          std.debug.print("PID found {} \n", .{kp[4..]});
                    has_pid = true;
                }
                if( std.mem.eql(u8, kp[0..3], "ecl")){
         //           std.debug.print("ECL found {} \n", .{kp[4..]});
                    has_ecl = true;
                }
                if( std.mem.eql(u8, kp[0..3], "eyr")){
           //         std.debug.print("eyr found {} \n", .{kp[4..]});
                    has_eyr = true;
                }
                if( std.mem.eql(u8, kp[0..3], "hcl")){
             //       std.debug.print("HCL found {} \n", .{kp[4..]});
                    has_hcl = true;
                }
                if( std.mem.eql(u8, kp[0..3], "byr")){
               //     std.debug.print("BYR found {} \n", .{kp[4..]});
                    has_byr = true;
                }
                if( std.mem.eql(u8, kp[0..3], "iyr")){
                 //   std.debug.print("IYR found {} \n", .{kp[4..]});
                    has_iyr = true;
                }
                if( std.mem.eql(u8, kp[0..3], "hgt")){
                   // std.debug.print("HGT found {} \n", .{kp[4..]});
                    has_hgt = true;
                }
         }
        }
        // check if all keys are true/present and increment
        if(
            has_ecl == true and
            has_pid == true and
            has_eyr == true and
            has_hcl == true and
            has_byr == true and
            has_iyr == true and
            has_hgt == true
        ){
            count += 1;
        }
        //reset key check
        has_ecl = false;
        has_pid = false;
        has_eyr = false;
        has_hcl = false;
        has_byr = false;
        has_iyr = false;
        has_hgt = false;
    }
    std.debug.print("Final count = {} \n", .{count});
}
