export function EuropeMap() {
  return (
    <div className="pointer-events-none flex origin-top-right items-start -translate-x-28 max-[1460px]:translate-x-0 max-[1150px]:translate-x-4 max-[1150px]:scale-[0.78]">
      <div className="relative">
        <div className="h-[118px] w-[330px] overflow-hidden max-[1150px]:h-[100px] max-[1150px]:w-[250px]">
          <img
            src="/country_map.png"
            alt="France, Germany, and the United Kingdom"
            className="-ml-2 h-[210px] w-auto max-w-none max-[1150px]:-ml-8 max-[1150px]:h-[180px]"
          />
        </div>
        <span className="absolute left-[108px] top-[92px] text-[13px] font-medium tracking-wide text-ink-secondary max-[1150px]:left-[72px] max-[1150px]:top-[78px] max-[1150px]:text-xs">
          France
        </span>
      </div>
      <div className="relative -ml-2 mt-1 w-[128px] shrink-0 max-[1150px]:-ml-10 max-[1150px]:w-[104px]">
        <p className="origin-left rotate-[-16deg] pt-1 text-left font-hand text-[15px] italic leading-[1.3] text-muted max-[1150px]:text-[13px] max-[1150px]:leading-[1.2]">
          <span className="block">3 markets</span>
          <span className="block">1 conversation</span>
          <span className="block">A clearer future</span>
        </p>
      </div>
    </div>
  );
}
