import { renderHook, act } from "@testing-library/react";
import { useInstitutions, Institution } from "@/hooks/useInstitutions";

import "whatwg-fetch";

describe("useInstitutions hook", () => {
  const fakeInstitutions: Institution[] = [
    { institution_id: "inst1", institution_name: "Bank A" },
    { institution_id: "inst2", institution_name: "Bank B" },
  ];

  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it("fetches institutions successfully", async () => {
    localStorage.setItem("token", "fake-token");

    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => fakeInstitutions,
    } as any);

    const { result } = renderHook(() => useInstitutions());

    expect(result.current.loading).toBe(true);

    await act(async () => {});

    expect(result.current.loading).toBe(false);
    expect(result.current.institutions).toEqual(fakeInstitutions);
  });

  it("handles missing token", async () => {
    const fetchSpy = jest.spyOn(global, "fetch");

    const { result } = renderHook(() => useInstitutions());

    await act(async () => {});

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
    expect(result.current.institutions).toEqual([]);
  });

  it("handles fetch failure gracefully", async () => {
    localStorage.setItem("token", "fake-token");

    jest.spyOn(global, "fetch").mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useInstitutions());

    await act(async () => {});

    expect(result.current.loading).toBe(false);
    expect(result.current.institutions).toEqual([]);
  });

  describe("getAccountsForInstitution", () => {
    it("fetches accounts successfully", async () => {
      localStorage.setItem("token", "fake-token");
      const fakeAccounts = [{ id: "acc1", name: "Checking" }];

      jest.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        json: async () => fakeInstitutions,
      } as any);

      const { result } = renderHook(() => useInstitutions());

      await act(async () => {});

      jest.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        json: async () => fakeAccounts,
      } as any);

      let accounts;
      await act(async () => {
        accounts = await result.current.getAccountsForInstitution("inst1");
      });

      expect(accounts).toEqual(fakeAccounts);
      expect(global.fetch).toHaveBeenLastCalledWith(
        "/api/bank/get-accounts?institution_id=inst1",
        expect.objectContaining({
          method: "POST",
          headers: { Authorization: "Bearer fake-token" },
        })
      );
    });

    it("returns null if token missing", async () => {
      const { result } = renderHook(() => useInstitutions());

      let accounts;
      await act(async () => {
        accounts = await result.current.getAccountsForInstitution("inst1");
      });

      expect(accounts).toBeNull();
    });

    it("returns null on fetch failure", async () => {
      localStorage.setItem("token", "fake-token");

      jest.spyOn(global, "fetch").mockRejectedValue(new Error("Network error"));

      const { result } = renderHook(() => useInstitutions());

      let accounts;
      await act(async () => {
        accounts = await result.current.getAccountsForInstitution("inst1");
      });

      expect(accounts).toBeNull();
    });
  });
});
