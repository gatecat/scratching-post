#![no_std]
#![no_main]

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::Config;
use embassy_stm32::gpio::{Level, Output, Speed, OutputType};

use embassy_stm32::timer::simple_pwm::{PwmPin, SimplePwm};
use embassy_stm32::timer::low_level::CountingMode;
use embassy_stm32::time::hz;

use embassy_time::Timer;
use {defmt_rtt as _, panic_probe as _};

#[embassy_executor::main]
async fn main(_spawner: Spawner) -> ! {
    let config = Config::default();
    let p = embassy_stm32::init(config);

    let mut led = Output::new(p.PB7, Level::High, Speed::Low);

    led.set_high();

    let servo_pin = PwmPin::new_ch4(p.PA3, OutputType::PushPull);
    let mut pwm = SimplePwm::new(p.TIM5, None, None, None, Some(servo_pin), hz(50), CountingMode::EdgeAlignedUp);

    let max_duty = pwm.max_duty_cycle();

    let servo_max = max_duty / 10;
    let servo_min = max_duty / 22;

    let mut ch4 = pwm.ch4();
    ch4.set_duty_cycle(servo_min);
    ch4.enable();
    loop {
        info!("Hello World!");
        led.set_high();
        for i in 0..5 {
            ch4.set_duty_cycle(servo_min + ((i * ((servo_max - servo_min) as u32)) / 5) as u16);
            Timer::after_millis(1000).await;
        }
    }
}