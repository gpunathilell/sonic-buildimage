command_name="sonic_bfb_installer"
usage(){
    echo "Syntax: $command_name -b|--bfb <BFB_Image_Path> --rshim|-r <rshim1,..rshimN> --verbose|-v --config|-c <Options> --dev-latest --dev-lastrc --prod-lastrc --prod-latest --help|h"
    echo "Arguments:"
    echo "-b			Provide custom path for bfb image"
    echo "-r			Install only on DPUs connected to rshim interfaces provided, mention all if installation is requried on all connected DPUs"
    echo "-v			Verbose installation result output"
    echo "-c			Config file"
    echo "-h		        Help"
}

bfb_install_call(){
    #Example:sudo bfb-install -b <full path to image> -r rshim<id>
    local result_file=$(mktemp "/tmp/result_file.XXXXX")
    local cmd="sudo ./bfb-install -b $2 -r $1 $appendix"
    echo "Installing bfb image on DPU connected to $1 using $cmd"
    local indicator="$1:"
    eval "$cmd" > "$result_file" 2>&1 > >(while IFS= read -r line; do echo "$indicator $line"; done > "$result_file")
    local exit_status=$?
    if [ $exit_status  -ne 0 ]; then
        echo "$1: Error: Installation failed on connected DPU!"
    else
        echo "$1: Installation Successful"
    fi
    if [ $exit_status -ne 0 ] ||[ $verbose = true ]; then
        cat "$result_file"
    fi
    rm -f "$result_file"
}

validate_rshim(){
    local provided_list=("$@")
    for item1 in "${provided_list[@]}"; do
        local found=0
        for item2 in "${dev_names_det[@]}"; do
            if [[ "$item1" = "$item2" ]]; then
                found=1
                break
            fi
        done
        if [[ $found -eq 0 ]]; then
            echo "$item1 is not detected! Please provide proper rshim interface list!"
            exit 1
        fi
    done
}

main(){
    local config=
    while [ "$1" != "--" ]  && [ -n "$1" ]; do
        case $1 in
            --help|-h)
                usage;
                exit 0
            ;;
            --bfb|-b)
                shift;
                bfb=$1
            ;;
            ;;
            --rshim|-r)
                shift;
                rshim_dev=$1
            ;;
            --config|-c)
                shift;
                config=$1
            ;;
            --verbose|-v)
                verbose=true
            ;;
        esac
        shift
    done
    if [ -z "$bfb" ]; then
        echo "Error : bfb image is not provided."
        usage
        exit 1
    fi
    if [[ -f ${config} ]]; then
        echo "Using ${config} file"
        appendix="-c ${config}"
    fi
    IFS=$'\n'
    dev_names_det+=($(ls /dev/rshim* | awk -F'/' '/^\/dev\/rshim/ {gsub(/:/,"",$NF); print $NF}'))
    if [ "${#dev_names_det[@]}" -eq 0 ]; then
        echo "No rshim interfaces detected! Make sure to run the $command_name script from the host device/ switch!"
        exit 1
    fi
    if [ -z "$rshim_dev" ]; then
        echo "No rshim interfaces provided!"
        usage
        exit 1
    else
        if [ "$rshim_dev" = "all" ]; then
            dev_names=("${dev_names_det[@]}")
            echo "${#dev_names_det[@]} rshim interfaces detected:"
            echo "${dev_names_det[@]}"
        else
            IFS=',' read -ra dev_names <<< "$rshim_dev"
            validate_rshim $dev_names
        fi
    fi
    for i in "${dev_names[@]}"
    do
        :
        bfb_install_call $i $bfb &
    done
    wait
}

appendix=
verbose=false
main "$@"
