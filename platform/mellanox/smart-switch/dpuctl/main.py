"""Click Implemenetation for dpuctl related commands"""
from multiprocessing import Process

try:
    import click
    from .dpuctl_hwm import DpuCtlPlat
except ImportError as e:
    raise ImportError(str(e) + '- required module not found') from e


def call_dpu_fw_upgrade(obj, path):
    """Function to call object specific firmware update for each dpu"""
    obj.dpu_fw_upgrade(path)


def call_dpu_reset(obj):
    """Function to call object specific Reset for each dpu"""
    obj.dpu_reboot()


def call_dpu_shutdown(obj):
    """Function to call object specific Shutdown for each dpu"""
    obj.dpu_shutdown()


def call_dpu_startup(obj):
    """Function to call object specific Startup for each dpu"""
    obj.dpu_startup()


def call_dpu_power_on(obj, force):
    """Function to call object specific power on for each dpu"""
    obj.dpu_power_on(force)


def call_dpu_power_off(obj, force):
    """Function to call object specific power off for each dpu"""
    obj.dpu_power_off(force)


def validate_return_dpus(all_dpus, dpu_names, dpuctl_list):
    """Function to validate list of dpus provided by User"""
    if (((not all_dpus) and (dpu_names is None)) or
            (all_dpus and (dpu_names is not None))):
        raise AssertionError("Invalid Arguments provided!"
                             "Please provide either dpu_names or -all option")

    if all_dpus:
        return [dpuctl_obj.get_name() for dpuctl_obj in dpuctl_list]
    existing_dpu_list = [dpuctl_obj.get_name() for dpuctl_obj in dpuctl_list]
    dpu_names_l = dpu_names.split(',')
    dpu_names_l = [dpu_name.strip() for dpu_name in dpu_names_l]
    for provided_dpu in dpu_names_l:
        if provided_dpu not in existing_dpu_list:
            raise AssertionError("Invalid Arguments provided!"
                                 f"{provided_dpu} does not exist!")
    return dpu_names_l


def execute_function_call(ctx,
                          all_dpus,
                          force,
                          dpu_names,
                          function_to_call,
                          path=None):
    """Function to fork multiple child process for each DPU
       and call required function"""
    dpuctl_list = ctx.obj['dpuctl_list']
    selected_dpus = validate_return_dpus(all_dpus, dpu_names, dpuctl_list)
    selected_dpus = list(set(selected_dpus))
    proc_list = []
    for dpu in dpuctl_list:
        if dpu.get_name() in selected_dpus:
            if function_to_call == "FW_UPG":
                if not path:
                    raise AssertionError("Path for FW image is empty!")
                proc = Process(target=call_dpu_fw_upgrade, args=(dpu, path))
            elif function_to_call == "PW_ON":
                proc = Process(target=call_dpu_power_on, args=(dpu, force))
            elif function_to_call == "PW_OFF":
                proc = Process(target=call_dpu_power_off, args=(dpu, force))
            elif function_to_call == "RST":
                proc = Process(target=call_dpu_reset, args=(dpu,))
            elif function_to_call == "SHTDN":
                proc = Process(target=call_dpu_shutdown, args=(dpu, ))
            elif function_to_call == "STRTUP":
                proc = Process(target=call_dpu_startup, args=(dpu, ))
            proc_list.append(proc)
    for proc in proc_list:
        proc.start()
    for proc in proc_list:
        proc.join()


@click.group()
@click.pass_context
def dpuctl(ctx=None):
    """SONiC command line - 'dpuctl' Wrapper command:
        Smart Switch DPU reset flow commands"""
    # TODO: Obtain list of dpus from platform.json
    existing_dpu_list = ['dpu1', 'dpu2', 'dpu3', 'dpu4']
    if len(existing_dpu_list) == 0:
        click.echo('No DPUs found! Please execute on switch!')
    click.echo(f"{existing_dpu_list} DPUs Present")
    dpuctl_list = []
    for dpu_name in existing_dpu_list:
        index = int(dpu_name[-1])-1
        dpuctl_list.append(DpuCtlPlat(index))
    context = {
        "dpuctl_list": dpuctl_list,
    }
    ctx.obj = context


@dpuctl.command(name='dpu-reset')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_reset(ctx, all_dpus, dpu_names=None):
    """Reset individual or all DPUs"""
    execute_function_call(ctx, all_dpus, None, dpu_names, "RST")


@dpuctl.command(name='dpu-power-on')
@click.option('--force', is_flag=True, default=False,
              help='Perform force power on - Turned off by default')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_power_on(ctx, force, all_dpus, dpu_names=None):
    """Power On individual or all DPUs"""
    execute_function_call(ctx, all_dpus, force, dpu_names, "PW_ON")


@dpuctl.command(name='dpu-startup')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_startup(ctx, all_dpus, dpu_names=None):
    """Start Up individual or all DPUs"""
    execute_function_call(ctx, all_dpus, None, dpu_names, "STRTUP")


@dpuctl.command(name='dpu-shutdown')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_shutdown(ctx, all_dpus, dpu_names=None):
    """Shutdown individual or all DPUs"""
    execute_function_call(ctx, all_dpus, None, dpu_names, "SHTDN")


@dpuctl.command(name='dpu-power-off')
@click.option('--force', is_flag=True, default=False,
              help='Perform force power off Turned of by default')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_power_off(ctx, force, all_dpus, dpu_names=None):
    """Power Off individual or all DPUs"""
    execute_function_call(ctx, all_dpus, force, dpu_names, "PW_OFF")


@dpuctl.command(name='dpu-fw-upgrade')
@click.option('--all',
              'all_dpus',
              is_flag=True,
              default=False,
              help='Execute for all DPUs')
@click.option('--path', 'fw_file_path', required=True, help='Path to fw image')
@click.argument('dpu_names', metavar='<dpu_names>', required=False)
@click.pass_context
def dpuctl_fw_upgrade(ctx, all_dpus, fw_file_path, dpu_names=None):
    """Firmware Upgrade individual or all DPUs"""
    execute_function_call(ctx,
                          all_dpus,
                          None,
                          dpu_names,
                          "FW_UPG",
                          fw_file_path)


if __name__ == '__main__':
    dpuctl()
