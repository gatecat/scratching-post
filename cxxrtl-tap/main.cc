#include "tap_demo.cc"
extern "C" {
#include "tapcfg/src/include/tapcfg.h"
}

#include <stdio.h>

#include <deque>
#include <mutex>

namespace {

    cxxrtl_design::p_top top;

    tapcfg_t *tapcfg;
    int fd;

    struct Packet {
        std::array<uint8_t, 2000> data;
        unsigned len;
    };

    std::deque<Packet> rx_queue;

    Packet tx_pkt;
    int rx_read_count = 0;

    // Based on https://github.com/enjoy-digital/litex/blob/master/litex/build/sim/core/modules/ethernet/ethernet.c
    static const unsigned char macadr[6] = {0xaa, 0xb6, 0x24, 0x69, 0x77, 0x21};

    void ethernet_init() {
        tapcfg = tapcfg_init();
        tapcfg_start(tapcfg, "tap0", 0);
        fd = tapcfg_get_fd(tapcfg);
        tapcfg_iface_set_hwaddr(tapcfg, reinterpret_cast<const char*>(macadr), 6);
        tapcfg_iface_set_ipv4(tapcfg, "192.168.49.1", 24);
        tapcfg_iface_set_status(tapcfg, TAPCFG_STATUS_ALL_UP);
    }

    void ethernet_handle_events() {
        if (tapcfg_wait_readable(tapcfg, 0)) {
            rx_queue.emplace_back();
            auto &pkt = rx_queue.back();
            pkt.len = tapcfg_read(tapcfg, pkt.data.data(), 2000);
            if (pkt.len < 60)
                pkt.len = 60;
        }
    }

    void ethernet_rx_tick(const value<1> &ready, value<1> &valid, value<9> &payload) {
        if (!rx_queue.empty()) {
            const auto &pkt = rx_queue.front();
            valid.set(true);
            // {last, data}
            payload.set(uint16_t((rx_read_count + 1) == pkt.len) << 8U | uint16_t(pkt.data[rx_read_count]));
            if (ready) {
                ++rx_read_count;
                if (rx_read_count == pkt.len) {
                    rx_queue.pop_front();
                    rx_read_count = 0;
                }
            }
        } else {
            valid.set(false);
            payload.set(0);
        }
    }

    // TODO: TX
};



int main(int argc, char *argv[]) {
    ethernet_init();
    top.step();
    long timestep = 0;
    while (true) {
        top.p_clk.set(false);
        top.step();
        top.p_clk.set(true);
        top.step();
        ethernet_rx_tick(top.p_rx____ready, top.p_rx____valid, top.p_rx____payload);

        ++timestep;
        if ((timestep % 100) == 0) {
            ethernet_handle_events();
        }
    }
}
