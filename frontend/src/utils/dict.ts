import DictAPI, { type DictDataTable } from "@/api/module_system/dict";

export const USER_SEX_DICT_TYPE = "sys_user_sex";

export type DictOption = DictDataTable & { dict_value: string };

/** Load enabled dictionary options in administrator-defined order. */
export async function fetchDictOptions(dictType: string): Promise<DictOption[]> {
  const response = await DictAPI.getInitDict(dictType);
  return (response.data.data || [])
    .filter((item): item is DictOption => item.status === "0" && item.dict_value != null)
    .sort((left, right) => (left.dict_sort || 0) - (right.dict_sort || 0));
}

export function getDictLabel(
  options: DictDataTable[],
  value: string | number | undefined,
): string {
  if (value == null || value === "") return "-";
  return options.find((item) => String(item.dict_value) === String(value))?.dict_label || String(value);
}

export function getDefaultDictValue(options: DictOption[]): string | undefined {
  return options.find((item) => item.is_default)?.dict_value || options[0]?.dict_value;
}
