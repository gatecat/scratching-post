package vexriscv

import spinal.core._
import spinal.core.internals.{ExpressionContainer, PhaseAllocateNames, PhaseContext}
import spinal.lib._
import spinal.lib.sim.Phase
import spinal.lib.com.jtag.Jtag

import vexriscv.ip.{DataCacheConfig, InstructionCacheConfig}
import vexriscv.plugin.CsrAccess.WRITE_ONLY
import vexriscv.plugin._

import scala.collection.mutable.ArrayBuffer

object SpinalConfig extends spinal.core.SpinalConfig(
  defaultConfigForClockDomains = ClockDomainConfig(
    resetKind = spinal.core.SYNC
  )) {
}


object GenCoreDefault{

  def main(args: Array[String]) {

    SpinalConfig.copy(netlistFileName = "VexRiscvLinuxAsic.v").generateVerilog {
      // Generate CPU plugin list
      val plugins = ArrayBuffer[Plugin[VexRiscv]]()

      plugins ++= List(
        new IBusCachedPlugin(
          resetVector = 0x100000, // 1MB
          relaxedPcCalculation = true,
          prediction = NONE,
          compressedGen = false,
          memoryTranslatorPortConfig = MmuPortConfig(portTlbSize = 4),
          config = InstructionCacheConfig(
            cacheSize = 512,
            bytePerLine = 32,
            wayCount = 1,
            addressWidth = 32,
            cpuDataWidth = 32,
            memDataWidth = 32,
            catchIllegalAccess = true,
            catchAccessFault = true,
            asyncTagMemory = false,
            twoCycleRam = false,
            twoCycleCache = true
          )
        ),
        new DBusCachedPlugin(
          dBusCmdMasterPipe = true,
          dBusCmdSlavePipe = true,
          dBusRspSlavePipe = false,
          relaxedMemoryTranslationRegister = false,
          config = new DataCacheConfig(
            cacheSize = 256,
            bytePerLine = 32,
            wayCount = 1,
            addressWidth = 32,
            cpuDataWidth = 32,
            memDataWidth = 32,
            catchAccessError = true,
            catchIllegal = true,
            catchUnaligned = true,
            withLrSc = true,
            withAmo = true,
            earlyWaysHits = true
          ),
          memoryTranslatorPortConfig = MmuPortConfig(portTlbSize = 4),
          csrInfo = true
        ),
        /* new DBusSimplePlugin(
          catchAddressMisaligned = true,
          catchAccessFault = true,
          withLrSc = true,
          memoryTranslatorPortConfig = MmuPortConfig(portTlbSize = 4)
        ),*/
        new MmuPlugin(
          ioRange = (x => x(31 downto 28) === 0xB || x(31 downto 28) === 0xE || x(31 downto 28) === 0xF)
        ),
        new DecoderSimplePlugin(
          catchIllegalInstruction = true
        ),
        new RegFilePlugin(
          regFileReadyKind = plugin.SYNC,
          zeroBoot = false
        ),
        new IntAluPlugin,
        new SrcPlugin(
          separatedAddSub = false,
          executeInsertion = true
        ),
        new FullBarrelShifterPlugin,
        new HazardSimplePlugin(
          bypassExecute           = true,
          bypassMemory            = true,
          bypassWriteBack         = true,
          bypassWriteBackBuffer   = true,
          pessimisticUseSrc       = false,
          pessimisticWriteRegFile = false,
          pessimisticAddressMatch = false
        ),
        new BranchPlugin(
          // If using CFU, use earlyBranch to avoid incorrect CFU execution
          earlyBranch = false,
          catchAddressMisaligned = true
        ),
        new CsrPlugin(
          CsrPluginConfig.linuxMinimal(mtVecInit = null).copy(ebreakGen = false)
        ),
        new MulDivIterativePlugin(
          genMul = true,
          genDiv = true,
          mulUnrollFactor = 1,
          divUnrollFactor = 1
        ),
        new ExternalInterruptArrayPlugin(
          machineMaskCsrId = 0xBC0,
          machinePendingsCsrId = 0xFC0,
          supervisorMaskCsrId = 0x9C0,
          supervisorPendingsCsrId = 0xDC0
        ),
        new DebugPlugin(ClockDomain.current.clone(reset = Bool().setName("debugReset"))),
        new YamlPlugin("VexRiscvLinuxAsic.yaml")
      )

      // CPU configuration
      val cpuConfig = VexRiscvConfig(plugins.toList)

      // CPU instantiation
      val cpu = new VexRiscv(cpuConfig)

      // CPU modifications to be an Wishbone
      cpu.rework {
        for (plugin <- cpuConfig.plugins) plugin match {
          case plugin: IBusSimplePlugin => {
            plugin.iBus.setAsDirectionLess() //Unset IO properties of iBus
            master(plugin.iBus.toWishbone()).setName("iBusWishbone")
          }
          case plugin: IBusCachedPlugin => {
            plugin.iBus.setAsDirectionLess()
            master(plugin.iBus.toWishbone()).setName("iBusWishbone")
          }
          case plugin: DBusSimplePlugin => {
            plugin.dBus.setAsDirectionLess()
            master(plugin.dBus.toWishbone()).setName("dBusWishbone")
          }
          case plugin: DBusCachedPlugin => {
            plugin.dBus.setAsDirectionLess()
            master(plugin.dBus.toWishbone()).setName("dBusWishbone")
          }
          case plugin: DebugPlugin => plugin.debugClockDomain {
            plugin.io.bus.setAsDirectionLess()
            val jtag = slave(new Jtag())
              .setName("jtag")
            jtag <> plugin.io.bus.fromJtag()
          }
          case _ =>
        }
      }

      cpu
    }
  }
}
