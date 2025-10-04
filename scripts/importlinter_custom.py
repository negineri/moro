"""This module defines a custom import linter contract."""

from grimp import ImportGraph, PackageDependency
from importlinter import Contract, ContractCheck, fields, output


class ModularMonolithContract(Contract):
    """Contract to check import constraints in a modular monolith structure."""

    root_package = fields.StringField()

    def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
        """Check the import constraints for the modular monolith structure."""
        output.verbose_print(verbose, f"Getting import details from {self.root_package} ...")
        modules = graph.find_children(f"{self.root_package}.modules")
        modules = {m for m in modules if m != f"{self.root_package}.modules.common"}
        deps = graph.find_illegal_dependencies_for_layers(
            layers=(
                f"{self.root_package}.cli",
                f"{self.root_package}.config",
                modules,
            )
        )
        import_exists = bool(deps)

        return ContractCheck(
            kept=not import_exists,
            metadata={
                "forbidden_import_details": deps,
            },
        )

    def render_broken_contract(self, check: ContractCheck) -> None:
        """Render the details of a broken contract."""
        output.print_error(
            "Violates the import constraint of a modular monolith.",
            bold=True,
        )
        output.new_line()
        for details in check.metadata["forbidden_import_details"]:
            if not isinstance(details, PackageDependency):
                raise TypeError("Expected PackageDependency instance.")
            for route in details.routes:
                output.print_error(f"{details.importer} -> {details.imported} via {route}")
                # output.print_error(details)
