from invoke import task


@task
def printer_info(ctx):
    """
    Prints Phomemo printer information.

    Printer must have been previously paired via Bluetooth.
    """

    from phomemo import Phomemo

    printer = Phomemo()
    info = printer.info
    if info:
        print(info)
    else:
        print("Printer not found or not connected.")


@task
def create_label(ctx, pn: int):
    """
    Create a label and save to file for the specified InvenTree part number.

    Args:
        pn (int): InvenTree part number.
    """

    from inventree import InvenTreePart, PartLabel

    part = InvenTreePart(num=pn)
    print(f"Generating label for part number: {pn} - {part.name}", flush=True)
    label = PartLabel(part=part)
    fn = label.to_file()
    print(f"Label saved to: {fn}")


@task
def print_label(ctx, filename: str):
    """
    Print a label image file to the Phomemo printer.

    Args:
        filename (str): Path to the label image file.
    """

    from phomemo import Phomemo

    printer = Phomemo()
    port = printer.port
    if port is None:
        print("Printer not connected. Please connect and try again.")
        return

    print(f"Printing label: {filename} to printer at {port}", flush=True)
    printer.print_file(filename)
    print("Print job sent.")
