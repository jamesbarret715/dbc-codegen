import sys
import functools
import operator

import cantools.database as dbc

extra_code = """
#define BUF_TO_INT(x) (((uint64_t)x[0]) | ((uint64_t)x[1] << 8) | ((uint64_t)x[2] << 16) | ((uint64_t)x[3] << 24) | ((uint64_t)x[4] << 32) | ((uint64_t)x[5] << 40) | ((uint64_t)x[6] << 48) | ((uint64_t)x[7] << 56))
#define BUF_TO_INT_REV(x) (((uint64_t)x[7]) | ((uint64_t)x[6] << 8) | ((uint64_t)x[5] << 16) | ((uint64_t)x[4] << 24) | ((uint64_t)x[3] << 32) | ((uint64_t)x[2] << 40) | ((uint64_t)x[1] << 48) | ((uint64_t)x[0] << 56))
"""


def smallest_int_type(size: int, signed: bool) -> str:
    prefix = "" if signed else "u"

    match size:
        case 1:
            return "bool"
        case x if 1 < x <= 8:
            return prefix + "int8_t"
        case x if 8 < x <= 16:
            return prefix + "int16_t"
        case x if 16 < x <= 32:
            return prefix + "int32_t"

    return prefix + "int_64_t"


def main():
    if len(sys.argv) <= 1:
        print(f"Usage: {sys.argv[0]} <dbc> [output]")
        exit(1)

    path, *args = sys.argv[1:]

    file = None

    if len(args) >= 1:
        file = open(args[0], "w")
        output = lambda *args, **kwargs: print(*args, file=file, **kwargs)
    else:
        output = print

    db = dbc.load_file(path)

    # Include guard
    output("#ifndef DBC_GENERATED_CODE")
    output("#define DBC_GENERATED_CODE")
    output()

    # Generate union frameId mask
    ids = [message.frame_id for message in db.messages]
    mask = functools.reduce(operator.or_, ids)

    output(f"#define DBC_FRAMEID_MASK 0x{mask:X}")

    # Insert any other code needed.
    output(extra_code)

    # Generate message<->frameId enum
    output("enum class Message : uint64_t")
    output("{")

    for message in db.messages:
        output(f"\t{message.name.upper()} = 0x{message.frame_id:X},")

    output("};")
    output()

    # Generate message structs and constructors
    for message in db.messages:
        output(f"struct {message.name}")
        output("{")

        for signal in message.signals:
            output(
                f"\t{smallest_int_type(signal.length, signal.is_signed)} {signal.name};",
                end="",
            )

            if signal.unit is not None:
                output(f' // Unit: "{signal.unit}"', end="")

            if signal.comment is not None:
                if signal.unit is None:
                    output(" //", end="")
                else:
                    output(",", end="")

                output(f' Comment: "{signal.comment.strip()}"', end="")

            output()

        output()
        output(f"\t{message.name}(uint8_t buf[8])")
        output("\t{")

        output(f"\t\tuint64_t data = BUF_TO_INT{"" if message.signals[0].byte_order == "little_endian" else "_REV"}(buf);")
        output()

        for signal in message.signals:
            output(f"\t\t{signal.name} = ", end="")

            converter = lambda x: (8 * (x // 8 + 1) - 1 - (x % 8))

            start_bit = (
                signal.start
                if signal.byte_order == "little_endian"
                else 64 - (converter(signal.start) + signal.length)
            )

            output(f"((data >> {start_bit}) & ((1 << {signal.length}) - 1))", end="")

            if signal.scale != 1:
                output(f" * ({signal.scale})", end="")

            if signal.offset != 0:
                output(f" + ({signal.offset})", end="")

            output(";")

        output("\t};")
        output("};")
        output()

    # Close include guard
    output("#endif // DBC_GENERATED_CODE")


if __name__ == "__main__":
    main()
