ATTACK CODE

This directory contains the actual code for implementing our proof of concept attacks against
MariaDB and MongoDB. Most of these files will repeatedly set up some test database, fill it with
some secret data, and attempt to use our attack techniques to extract that data. These files output
CSV files containing data about how accurate each attack trial run was.

We recommend using the scripts in the experiments directory to run the experiments, as they have
an easier to use interface. But feel free to dig into this code to see how our attacks could be
implemented in practice.

