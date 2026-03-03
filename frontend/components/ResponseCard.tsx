import { PredictResponse } from "@/types/prediction";
import MetadataPanel from "./MetadataPanel";

export default function ResponseCard({
  data,
}: {
  data: PredictResponse;
}) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-md space-y-4">
      <div className="whitespace-pre-wrap">
        {data.output}
      </div>

      <MetadataPanel data={data} />
    </div>
  );
}