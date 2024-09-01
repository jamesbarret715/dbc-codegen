# DBC Codegen
A utility script to generate a static C++ header for decoding CAN frames based on a [Vektor DBC file](https://www.csselectronics.com/pages/can-dbc-file-database-intro).

# Usage
Run the script to generate the header. By default, it outputs to `stdout`.
```bash
$ python ./generate.py DBC_PATH OPTIONAL_OUTPUT_PATH
```

Include the generated code in your C++ project.
```c++
#include "generated.h"
```

Two major objects are generated, the `Message` enum, and corresponding structs.  

You can compare frame IDs to the enum to associate them to a message, and use the corresponding struct to make use of the data enclosed in the frame.
```c++
unsigned long id;
unsigned char buf[8];

// Get your CAN frame using an adapter or otherwise.

// Now, you can associate the ID to a DBC message
switch ((Message)id) 
{
case Message::YOUR_DBC_MESSAGE:
{
    // and use the struct type to make use of the data.
    const Your_DBC_Message msg(buf);

    std::cout << msg.someSignal << std::endl;

    break;
}   
}
```

Additionally, a constant `DBC_FRAMEID_MASK` is also generated, which is the bitwise OR of all the included messages' frame IDs. This can be used to discard frames that aren't defined in your DBC.

```c++
if (id & DBC_FRAMEID_MASK != id) return;
```