import argparse
import subprocess

parser = argparse.ArgumentParser(description="Run experiments to test precision of k of n DBREACH attack")

parser.add_argument("--db", dest="database", action="store", choices={"MongoDB", "MariaDB"}, help="database to use", required = True)

parser.add_argument("--out", dest="outfile", action="store", help="output file to write results to", required=True)

parser.add_argument("--data-type", dest="datatype", action="store", choices={"random", "english", "emails"}, help="type of data to extract from DB", required=True)

parser.add_argument("--compress", dest="compress_algo", action="store", choices={"snappy", "zlib", "lz4"}, help="compression algorithm to use (MongoDB does not support LZ4)", required=True)

parser.add_argument("--mode", dest="mode", action="store", choices={"demo", "complete"}, help="whether to perform all tests or just demo. Demo only tests attack with 1 secret inserted, whereas complete tests with different numbers", default="demo")

args = parser.parse_args()

if (args.database == "MongoDB"):
    if args.compress_algo == "lz4":
        raise Exception("MongoDB does not support the LZ4 compression algorithm")
    python_args = ["python3", "-u", "../attack_code/test_decision_attack_mongo.py", "--" + args.datatype, "--" + args.compress_algo]
    if args.mode == "demo":
        python_args += ["--num_secrets", "1"]
    else:
        python_args += ["--num_secrets" "1", "20", "40", "60", "80", "100", "120", "140", "160", "180", "200", "220", "240"]
    subprocess.run(python_args, stdout=open(args.outfile, "a"))
elif (args.database == "MariaDB"):
    python_args = ["python3", "-u", "../attack_code/test_decision_attack_maria.py", "--" + args.datatype]
    if args.mode == "demo":
        python_args += ["--num_secrets", "1"]
    else:
        python_args += ["--num_secrets" "1", "20", "40", "60", "80", "100", "120", "140", "160", "180", "200", "220", "240"]
    print("WARNING: Prior to running this program with MariaDB, make sure your DB compression configuration matches the requested compression algorithm")
    subprocess.run(python_args, stdout=open(args.outfile, "a"))
