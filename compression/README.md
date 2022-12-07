COMPRESSION TEST FILES

This directory contains python programs for testing the behavior of certain compression algorithms.

These programs are not involved in any of the DBREACH attacks, but were useful for seeing how
strings grow as additional compressible characters are added. We relied on this information, as
well as empirical data from trying different attacks, to decide on the ultimate format for our
"filler" and "compressor" strings, to which we append or remove compressible characters in order
to change the size of the compressed table.

