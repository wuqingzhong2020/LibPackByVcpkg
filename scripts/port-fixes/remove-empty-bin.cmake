# Linux 下 OMPL/VTK 的共享库在 lib；官方配方收尾后只删除确实为空的 bin。
foreach(directory IN ITEMS bin debug/bin)
    set(path "${CURRENT_PACKAGES_DIR}/${directory}")
    file(GLOB contents "${path}/*")
    if(IS_DIRECTORY "${path}" AND NOT contents)
        file(REMOVE_RECURSE "${path}")
    endif()
endforeach()
