import { renderHook, act } from "@testing-library/react";
import { useAccounts } from "@/hooks/useAccounts";

import "whatwg-fetch";

describe("useAccounts", () => {
  const fakeAccounts = [
    { id: "1", name: "Checking", type: "bank", balance: 100, transactions: [] },
    { id: "2", name: "Savings", type: "bank", balance: 500, transactions: [] },
  ];

  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it("fetches accounts successfully", async () => {
    localStorage.setItem("token", "fake-token");

    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    const { result } = renderHook(() => useAccounts());

    await act(async () => {
      await result.current.fetchAccounts();
    });

    expect(result.current.accounts).toEqual(fakeAccounts);
    expect(result.current.loading).toBe(false);
  });

  it("does nothing if no token", async () => {
    const fetchSpy = jest.spyOn(global, "fetch");

    const { result } = renderHook(() => useAccounts());

    await act(async () => {
      await result.current.fetchAccounts();
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.current.accounts).toEqual([]);
    expect(result.current.loading).toBe(true);
  });

  it("deletes an account successfully", async () => {
    localStorage.setItem("token", "fake-token");

    const { result } = renderHook(() => useAccounts());

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    await act(async () => result.current.fetchAccounts());

    jest.spyOn(window, "confirm").mockReturnValue(true);

    jest.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true } as any);

    await act(async () => {
      await result.current.deleteAccount("1");
    });

    expect(result.current.accounts).toEqual([fakeAccounts[1]]);
    expect(result.current.deleting).toBeNull();
  });

  it("cancels deletion if user declines confirm", async () => {
    localStorage.setItem("token", "fake-token");

    const { result } = renderHook(() => useAccounts());

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    await act(async () => {
      await result.current.fetchAccounts();
    });

    jest.spyOn(window, "confirm").mockReturnValue(false);

    const fetchSpy = jest.spyOn(global, "fetch");

    await act(async () => {
      await result.current.deleteAccount("1");
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);

    expect(result.current.accounts).toEqual(fakeAccounts);
  });


  it("alerts on deletion failure", async () => {
    localStorage.setItem("token", "fake-token");

    const { result } = renderHook(() => useAccounts());

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    await act(async () => result.current.fetchAccounts());

    jest.spyOn(window, "confirm").mockReturnValue(true);

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Failed!" }),
    } as any);

    const alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});

    await act(async () => {
      await result.current.deleteAccount("1");
    });

    expect(alertSpy).toHaveBeenCalledWith("Failed to delete account: Failed!");
    expect(result.current.accounts).toEqual(fakeAccounts);
  });

  it("edits an account successfully", async () => {
    localStorage.setItem("token", "fake-token");

    const { result } = renderHook(() => useAccounts());

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    await act(async () => {
      await result.current.fetchAccounts();
    });

    jest.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true } as any);

    await act(async () => {
      await result.current.editAccount("1", "New Checking");
    });

    expect(result.current.accounts).toEqual([
      { ...fakeAccounts[0], name: "New Checking" },
      fakeAccounts[1],
    ]);

    expect(result.current.editing).toBeNull();
  });

  it("alerts on edit failure", async () => {
    localStorage.setItem("token", "fake-token");

    const { result } = renderHook(() => useAccounts());

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ accounts: fakeAccounts }),
    } as any);

    await act(async () => {
      await result.current.fetchAccounts();
    });

    jest.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Update failed" }),
    } as any);

    const alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});

    await act(async () => {
      await result.current.editAccount("1", "Broken Name");
    });

    expect(alertSpy).toHaveBeenCalledWith(
      "Failed to update account: Update failed"
    );

    expect(result.current.accounts).toEqual(fakeAccounts);
    expect(result.current.editing).toBeNull();
  });

  it("does nothing when editing without token", async () => {
    const fetchSpy = jest.spyOn(global, "fetch");

    const { result } = renderHook(() => useAccounts());

    await act(async () => {
      await result.current.editAccount("1", "New Name");
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.current.editing).toBeNull();
  });
});
