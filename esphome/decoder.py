def decode(hex_string):
    b = bytes.fromhex(hex_string)

    if len(b) != 9:
        raise ValueError("Expected 9 bytes")

    obj_id = b[0]

    tmp_lo = int.from_bytes(b[1:3], "little")
    tmp_hi = int.from_bytes(b[3:5], "little")
    hm_lo  = int.from_bytes(b[5:7], "little")
    hm_hi  = int.from_bytes(b[7:9], "little")

    print(f"object id : 0x{obj_id:02x}")
    print(f"tmp_lo    : {tmp_lo} ({tmp_lo/100:.2f} °C)")
    print(f"tmp_hi    : {tmp_hi} ({tmp_hi/100:.2f} °C)")
    print(f"hm_lo     : {hm_lo} ({hm_lo/100:.2f} %)")
    print(f"hm_hi     : {hm_hi} ({hm_hi/100:.2f} %)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Decode MiThermometer data")
    parser.add_argument("hex_string", help="Hex string to decode")
    args = parser.parse_args()

    decode(args.hex_string)