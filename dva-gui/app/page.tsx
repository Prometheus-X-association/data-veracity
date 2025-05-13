import Image from "next/image";

export default async function Home() {
  const endpoint = `${process.env.DVA_API_HOST}/info/attestations`
  let exchanges: Any[] = []
  try {
    const exchangeData = await fetch(endpoint)
    exchanges = await exchangeData.json()
  } catch (e) {
    console.log(`Failed to fetch info from ${endpoint}`, e)
  }
  return (
    <div>
      <div className="flex justify-around items-center mx-auto p-[16px] bg-white font-[family-name:var(--font-geist-sans)]">
	<Image src="/logo-bme.png" alt="BME logo" width={200} height={50} />
	<h1 className="text-3xl">Data Veracity Assurance</h1>
        <Image src="/logo-ptx.png" alt="Prometheus-X logo" width={200} height={50} />
      </div>
      <div className="min-h-[60vh]">
        <main className="m-auto pt-[40px] pb-[140px] max-w-[1200px]">
	  <div className="flex flex-col justify-start items-stretch gap-[8px]">
	    <h2 className="text-xl">Exchanges</h2>
	    <ul>
	      {exchanges.map((x) => (
                <li key={x.contract}>Contract: {x.contract}; Data processing ID: {x.dataProcessingID}</li>
	      ))}
	    </ul>
	  </div>
        </main>
      </div>
      <div className="py-10 bg-blue-950 text-white">
        <footer className="p-8">
	  <p>© Copyright BME 2025</p>
        </footer>
      </div>
   </div>
  );
}
