# Create an INTERFACE library for our C module.
add_library(mahony INTERFACE)

# Add our source files to the lib
target_sources(mahony INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/mahony.c
    ${CMAKE_CURRENT_LIST_DIR}/../invsqrt/invsqrt.c
)

# Add the current directory as an include directory.
target_include_directories(mahony INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE mahony)
