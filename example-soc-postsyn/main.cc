#undef NDEBUG

#include "verilated.h"
#include "Vsim_top.h"
#include "models/models.h"

#include <fstream>
#include <filesystem>

int main(int argc, char **argv) {
    VerilatedContext* contextp = new VerilatedContext;
    contextp->commandArgs(argc, argv);

    // Verilated::traceEverOn(true);

    Vsim_top *top = new Vsim_top{contextp};

    spiflash_model flash("flash", &top->soc_flash_clk, &top->soc_flash_csn,
        &top->soc_flash_d_o, &top->soc_flash_d_oe, &top->soc_flash_d_i);

    uart_model uart_0("uart_0", &top->soc_uart_0_tx, &top->soc_uart_0_rx);

    gpio_model gpio_0("gpio_0", &top->soc_gpio_0_gpio_o, &top->soc_gpio_0_gpio_oe, &top->soc_gpio_0_gpio_i);

    open_event_log("events.json");
    open_input_commands("input.json");

    unsigned timestamp = 0;
    auto tick = [&]() {
        // agent.print(stringf("timestamp %d\n", timestamp), CXXRTL_LOCATION);

        flash.step(timestamp);
        uart_0.step(timestamp);

        gpio_0.step(timestamp);

        top->clk = 0;
        contextp->timeInc(1);
        top->eval();
        ++timestamp;

        top->clk = 1;
        contextp->timeInc(1);
        top->eval();
        ++timestamp;

        // if (timestamp == 10)
        //     agent.breakpoint(CXXRTL_LOCATION);
    };

    flash.load_data("software.bin", 0x00100000U);


    top->rst_n = 0;
    tick();

    top->rst_n = 1;
    for (int i = 0; i < 3000000; i++)
        tick();

    close_event_log();
    delete top;
    delete contextp;
    return 0;
}
